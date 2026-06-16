import os
import logging
from datetime import datetime, timezone, timedelta

import requests
from celery import shared_task
from django.utils import timezone as dj_timezone

from django.db import models
from partidas.models import Partida

logger = logging.getLogger(__name__)

BASE_URL = 'https://sofascore6.p.rapidapi.com/api/sofascore'
SEASON_ID = 58210
TOURNAMENT_ID = 16

STATUS_MAP = {
    'notstarted': Partida.Status.NAO_INICIADA,
    'inprogress': Partida.Status.EM_ANDAMENTO,
    'finished': Partida.Status.FINALIZADA,
    'postponed': Partida.Status.ADIADA,
    'canceled': Partida.Status.CANCELADA,
    'cancelled': Partida.Status.CANCELADA,
}

TEMPO_TRADUCAO = {
    '1st half': '1º Tempo',
    'Halftime': 'Intervalo',
    '2nd half': '2º Tempo',
    'Ended': 'Encerrado',
    'AET': 'Prorrogação',
    'Penalties': 'Pênaltis',
    'Interrupted': 'Interrompido',
    'Postponed': 'Adiado',
}

INCIDENTE_TRADUCAO = {
    'regular': 'Normal',
    'penalty': 'Pênalti',
    'ownGoal': 'Gol Contra',
    'yellow': 'Amarelo',
    'red': 'Vermelho',
    'yellowRed': '2º Amarelo',
    'Foul': 'Falta',
    'Time wasting': 'Cera',
    'Argument': 'Reclamação',
    'Professional foul last man': 'Falta profissional',
    'Handball': 'Toque de mão',
}


def _get_headers():
    API_KEY = os.environ.get('RAPID_API_KEY')
    if not API_KEY:
        raise ValueError('RAPID_API_KEY não encontrada nas variáveis de ambiente.')
    return {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'sofascore6.p.rapidapi.com',
        'Content-Type': 'application/json',
    }


def _buscar_incidentes(event_id, headers):
    url = f'{BASE_URL}/v1/match/incidents'
    params = {'match_id': event_id}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f'Erro ao buscar incidentes da partida {event_id}: {e}')
        return None

    data = response.json()
    incidents = data if isinstance(data, list) else data.get('incidents', [])

    gols = []
    cartoes = []

    for inc in incidents:
        inc_type = inc.get('incidentType', '').lower()
        player = inc.get('player', {})
        player_name = player.get('name') or player.get('shortName', 'Desconhecido')
        minute = inc.get('time')
        is_home = inc.get('isHome', None)

        if inc_type == 'goal':
            gols.append({
                'jogador': player_name,
                'minuto': minute,
                'time': 1 if is_home else 2,
                'tipo': INCIDENTE_TRADUCAO.get(inc.get('incidentClass', 'regular'), inc.get('incidentClass', 'Normal')),
            })

        elif inc_type == 'card':
            cartoes.append({
                'jogador': player_name,
                'minuto': minute,
                'time': 1 if is_home else 2,
                'tipo': INCIDENTE_TRADUCAO.get(inc.get('incidentClass', ''), inc.get('incidentClass', '')),
                'motivo': INCIDENTE_TRADUCAO.get(inc.get('reason', ''), inc.get('reason', '')),
            })

        elif inc_type == 'inGamePenalty':
            gols.append({
                'jogador': player_name,
                'minuto': minute,
                'time': 1 if is_home else 2,
                'tipo': 'Pênalti',
            })

    return {
        'gols': gols,
        'cartoes': cartoes,
    }


def _parse_events(response_data):
    if isinstance(response_data, list):
        return response_data
    return response_data.get('events', [])


@shared_task()
def atualizar_partidas_ao_vivo():
    agora = dj_timezone.localtime()
    fim_do_dia = agora.replace(hour=23, minute=59, second=59, microsecond=999999)

    partidas = Partida.objects.filter(
        data__lte=fim_do_dia,
    ).exclude(
        status__in=[Partida.Status.FINALIZADA, Partida.Status.CANCELADA]
    )

    if not partidas.exists():
        logger.info('Nenhuma partida para atualizar.')
        return 'Nenhuma partida para atualizar.'

    limite = agora + timedelta(minutes=2)
    tem_jogo_proximo = partidas.filter(
        models.Q(status=Partida.Status.EM_ANDAMENTO) |
        models.Q(data__lte=limite)
    ).exists()

    if not tem_jogo_proximo:
        logger.info('Nenhuma partida próxima de começar.')
        return 'Nenhuma partida próxima de começar.'

    headers = _get_headers()

    rounds_to_check = set(partidas.values_list('fase', flat=True))
    round_events = {}

    for fase in rounds_to_check:
        try:
            round_num = int(fase.split()[-1])
        except (ValueError, IndexError):
            continue

        url = f'{BASE_URL}/v1/unique-tournament/season/round/matches'
        params = {
            'round': round_num,
            'season_id': SEASON_ID,
            'unique_tournament_id': TOURNAMENT_ID,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            events = _parse_events(response.json())

            for event in events:
                round_events[event['id']] = event

        except requests.RequestException as e:
            logger.error(f'Erro ao buscar round {round_num}: {e}')

    atualizadas = 0

    for partida in partidas:
        event = round_events.get(partida.id_api)
        if not event:
            continue

        home_score = event.get('homeScore') or {}
        away_score = event.get('awayScore') or {}
        partida.placar_1 = home_score.get('current') if isinstance(home_score, dict) else None
        partida.placar_2 = away_score.get('current') if isinstance(away_score, dict) else None

        status_info = event.get('status', {})
        status_type = status_info.get('type', '').lower()
        partida.status = STATUS_MAP.get(status_type, partida.status)

        desc_original = status_info.get('description', '')
        partida.tempo = TEMPO_TRADUCAO.get(desc_original, desc_original)

        if status_type in ('inprogress', 'finished'):
            estatisticas = _buscar_incidentes(partida.id_api, headers)
            if estatisticas:
                partida.estatisticas_finais = estatisticas

        partida.save()
        atualizadas += 1
        logger.info(
            f'Partida {partida.time_1} x {partida.time_2}: '
            f'{partida.placar_1}-{partida.placar_2} ({partida.tempo})'
        )

    return f'{atualizadas} partida(s) atualizada(s).'


@shared_task()
def importar_partidas(rounds=None):
    if rounds is None:
        rounds = list(range(1, 4))

    headers = _get_headers()

    total_criadas = 0
    total_atualizadas = 0

    for round_num in rounds:
        logger.info(f'Buscando partidas do round {round_num}...')

        url = f'{BASE_URL}/v1/unique-tournament/season/round/matches'
        params = {
            'round': round_num,
            'season_id': SEASON_ID,
            'unique_tournament_id': TOURNAMENT_ID,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f'Erro ao buscar round {round_num}: {e}')
            continue

        events = _parse_events(response.json())

        if not events:
            logger.warning(f'Nenhuma partida encontrada no round {round_num}.')
            continue

        for event in events:
            try:
                id_api = event['id']
                time_1 = event.get('homeTeam', {}).get('name', 'Desconhecido')
                time_2 = event.get('awayTeam', {}).get('name', 'Desconhecido')

                home_score = event.get('homeScore') or {}
                away_score = event.get('awayScore') or {}
                placar_1 = home_score.get('current') if isinstance(home_score, dict) else None
                placar_2 = away_score.get('current') if isinstance(away_score, dict) else None

                timestamp = event.get('timestamp')
                data = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                status_info = event.get('status', {})
                status_type = status_info.get('type', '').lower()
                status = STATUS_MAP.get(status_type, Partida.Status.NAO_INICIADA)

                _, created = Partida.objects.update_or_create(
                    id_api=id_api,
                    defaults={
                        'time_1': time_1,
                        'time_2': time_2,
                        'placar_1': placar_1,
                        'placar_2': placar_2,
                        'data': data,
                        'status': status,
                        'fase': f'Rodada {round_num}',
                    },
                )

                if created:
                    total_criadas += 1
                else:
                    total_atualizadas += 1

            except (KeyError, TypeError, ValueError) as e:
                logger.warning(f'Erro ao processar evento {event.get("id", "?")}: {e}')

        logger.info(f'Round {round_num}: {len(events)} partidas processadas.')

    resultado = f'{total_criadas} criadas, {total_atualizadas} atualizadas.'
    logger.info(f'Importação concluída! {resultado}')
    return resultado