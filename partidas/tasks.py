import logging
from datetime import datetime, time, timedelta, timezone

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone as dj_timezone


from partidas.models import Partida

logger = logging.getLogger(__name__)

BASE_URL = 'https://sofascore6.p.rapidapi.com/api/sofascore'

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
    api_key = settings.RAPID_API_KEY
    if not api_key:
        raise ValueError('RAPID_API_KEY não encontrada nas configurações.')
    return {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'sofascore6.p.rapidapi.com',
        'Content-Type': 'application/json',
    }


def _buscar_incidentes(event_id, headers):
    url = f'{BASE_URL}/v1/match/incidents'
    params = {'match_id': event_id}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f'Erro de rede ao buscar incidentes da partida {event_id}: {e}')
        return None
    except ValueError:
        logger.error(f'A API não retornou um JSON válido para a partida {event_id}')
        return None

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
            classe_incidente = inc.get('incidentClass', 'regular')
            tipo_traduzido = INCIDENTE_TRADUCAO.get(classe_incidente, classe_incidente.capitalize())
            gols.append({
                'jogador': player_name,
                'minuto': minute,
                'time': 1 if is_home else 2,
                'tipo': tipo_traduzido,
            })

        elif inc_type == 'card':
            classe_incidente = inc.get('incidentClass', '')
            tipo_traduzido = INCIDENTE_TRADUCAO.get(classe_incidente, classe_incidente.capitalize())
            motivo_original = inc.get('reason', '')
            motivo_traduzido = INCIDENTE_TRADUCAO.get(motivo_original, motivo_original)
            cartoes.append({
                'jogador': player_name,
                'minuto': minute,
                'time': 1 if is_home else 2,
                'tipo': tipo_traduzido,
                'motivo': motivo_traduzido,
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


def _extrair_rodada_numero(fase):
    if not fase:
        return None
    try:
        return int(fase.split()[-1])
    except (ValueError, IndexError):
        return None


@shared_task()
def atualizar_incidentes(partida_id_api):
    headers = _get_headers()
    estatisticas = _buscar_incidentes(partida_id_api, headers)

    if estatisticas:
        updated = Partida.objects.filter(id_api=partida_id_api).update(
            estatisticas_finais=estatisticas
        )
        if updated:
            logger.info(f'Incidentes atualizados para a partida {partida_id_api}.')
        else:
            logger.warning(f'Partida {partida_id_api} não encontrada ao salvar incidentes.')
    else:
        logger.warning(f'Nenhum incidente retornado para a partida {partida_id_api}.')


@shared_task()
def atualizar_partidas():
    agora = dj_timezone.localtime()
    inicio_do_dia = dj_timezone.make_aware(
        datetime.combine(agora.date(), time.min),
        timezone=agora.tzinfo,
    )
    fim_do_dia = dj_timezone.make_aware(
        datetime.combine(agora.date(), time.max),
        timezone=agora.tzinfo,
    )

    partidas = list(
        Partida.objects.filter(
            data__range=(inicio_do_dia, fim_do_dia),
        ).exclude(
            status__in=[Partida.Status.FINALIZADA, Partida.Status.CANCELADA]
        )
    )

    if not partidas:
        logger.info('Nenhuma partida para atualizar.')
        return 'Nenhuma partida para atualizar.'

    limite = agora + timedelta(minutes=2)
    tem_jogo_proximo = any(
        p.status == Partida.Status.EM_ANDAMENTO or p.data <= limite
        for p in partidas
    )

    if not tem_jogo_proximo:
        logger.info('Nenhuma partida próxima de começar.')
        return 'Nenhuma partida próxima de começar.'

    headers = _get_headers()

    season_id = settings.SOFASCORE_SEASON_ID
    tournament_id = settings.SOFASCORE_TOURNAMENT_ID

    rounds_to_check = {p.rodada for p in partidas if p.rodada is not None}

    if not rounds_to_check:
        for p in partidas:
            num = _extrair_rodada_numero(p.fase)
            if num is not None:
                rounds_to_check.add(num)

    round_events = {}

    for round_num in rounds_to_check:
        url = f'{BASE_URL}/v1/unique-tournament/season/round/matches'
        params = {
            'round': round_num,
            'season_id': season_id,
            'unique_tournament_id': tournament_id,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f'Erro ao buscar round {round_num}: {e}')
            continue
        except ValueError:
            logger.error(f'A API não retornou um JSON válido para o round {round_num}')
            continue

        events = _parse_events(data)
        for event in events:
            round_events[event['id']] = event

    partidas_atualizadas = []
    partidas_notificaveis = []

    for partida in partidas:
        event = round_events.get(partida.id_api)
        if not event:
            continue

        old_placar_1 = partida.placar_1
        old_placar_2 = partida.placar_2
        old_status = partida.status

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
            atualizar_incidentes.delay(partida.id_api)

        partidas_atualizadas.append(partida)
        
        if old_placar_1 != partida.placar_1 or old_placar_2 != partida.placar_2 or old_status != partida.status:
            partidas_notificaveis.append(partida)

        logger.info(
            f'Partida {partida.time_1} x {partida.time_2}: '
            f'{partida.placar_1}-{partida.placar_2} ({partida.tempo})'
        )

    if partidas_atualizadas:
        Partida.objects.bulk_update(
            partidas_atualizadas,
            ['placar_1', 'placar_2', 'status', 'tempo']
        )
        if partidas_notificaveis:
            try:
                from notificacao.signals import criar_notificacoes_para_partidas
                criar_notificacoes_para_partidas(partidas_notificaveis)
            except Exception as e:
                logger.error(f"Erro ao disparar notificações de partidas atualizadas: {e}")

    return f'{len(partidas_atualizadas)} partida(s) atualizada(s).'


@shared_task()
def importar_partidas(rounds):
    headers = _get_headers()

    season_id = settings.SOFASCORE_SEASON_ID
    tournament_id = settings.SOFASCORE_TOURNAMENT_ID

    total_criadas = 0
    total_atualizadas = 0

    for round_num in rounds:
        logger.info(f'Buscando partidas do round {round_num}...')

        url = f'{BASE_URL}/v1/unique-tournament/season/round/matches'
        params = {
            'round': round_num,
            'season_id': season_id,
            'unique_tournament_id': tournament_id,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f'Erro ao buscar round {round_num}: {e}')
            continue
        except ValueError:
            logger.error(f'A API não retornou um JSON válido para o round {round_num}')
            continue

        events = _parse_events(data)

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
                data_partida = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                status_info = event.get('status', {})
                status_type = status_info.get('type', '').lower()
                status = STATUS_MAP.get(status_type, Partida.Status.NAO_INICIADA)

                desc_original = status_info.get('description', '')
                tempo = TEMPO_TRADUCAO.get(desc_original, desc_original) if desc_original else None

                partida_existente = Partida.objects.filter(id_api=id_api).first()
                estatisticas_atuais = partida_existente.estatisticas_finais if partida_existente else None

                _, created = Partida.objects.update_or_create(
                    id_api=id_api,
                    defaults={
                        'time_1': time_1,
                        'time_2': time_2,
                        'placar_1': placar_1,
                        'placar_2': placar_2,
                        'data': data_partida,
                        'status': status,
                        'tempo': tempo,
                        'estatisticas_finais': estatisticas_atuais,
                        'fase': f'Rodada {round_num}',
                        'rodada': round_num,
                    },
                )

                if status_type in ('inprogress', 'finished'):
                    if not (status_type == 'finished' and estatisticas_atuais):
                        atualizar_incidentes.delay(id_api)

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