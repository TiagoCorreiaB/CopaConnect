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

FASE_TRADUCAO = {
    'Round of 32': 'Dezesseis avos de final',
    'Round of 16': 'Oitavas de final',
    'Quarterfinals': 'Quartas de final',
    'Quarterfinal': 'Quartas de final',
    'Semifinals': 'Semifinais',
    'Semifinal': 'Semifinais',
    'Final': 'Final',
    '3rd place': 'Disputa de 3º lugar',
    'Third place': 'Disputa de 3º lugar',
}

TIMES_TRADUCAO = {
    'Germany': 'Alemanha',
    'Paraguay': 'Paraguai',
    'France': 'França',
    'Sweden': 'Suécia',
    'South Africa': 'África do Sul',
    'Canada': 'Canadá',
    'Netherlands': 'Holanda',
    'Morocco': 'Marrocos',
    'Portugal': 'Portugal',
    'Croatia': 'Croácia',
    'Spain': 'Espanha',
    'Austria': 'Áustria',
    'Brazil': 'Brasil',
    'Argentina': 'Argentina',
    'Italy': 'Itália',
    'England': 'Inglaterra',
    'Belgium': 'Bélgica',
    'Uruguay': 'Uruguai',
    'Switzerland': 'Suíça',
    'Senegal': 'Senegal',
    'USA': 'Estados Unidos',
    'United States': 'Estados Unidos',
    'Mexico': 'México',
    'Poland': 'Polônia',
    'Australia': 'Austrália',
    'Japan': 'Japão',
    'South Korea': 'Coreia do Sul',
    'Korea Republic': 'Coreia do Sul',
    'Saudi Arabia': 'Arábia Saudita',
    'Qatar': 'Catar',
    'Ecuador': 'Equador',
    'Iran': 'Irã',
    'Wales': 'País de Gales',
    'Denmark': 'Dinamarca',
    'Tunisia': 'Tunísia',
    'Costa Rica': 'Costa Rica',
    'Cameroon': 'Camarões',
    'Serbia': 'Sérvia',
    'Ghana': 'Gana',
    'Norway': 'Noruega',
    "Côte d'Ivoire": "Costa do Marfim",
    'DR Congo': 'RD Congo',
    'Egypt': 'Egito',
    'Algeria': 'Argélia',
    'Colombia': 'Colômbia',
    'Bosnia & Herzegovina': 'Bósnia e Herzegovina',
    'Cabo Verde': 'Cabo Verde',
}


def _traduzir_time(name):
    if not name:
        return name
    if name in TIMES_TRADUCAO:
        return TIMES_TRADUCAO[name]
    if name.startswith('W') and name[1:].isdigit():
        return f'Vencedor {name[1:]}'
    if name.startswith('L') and name[1:].isdigit():
        return f'Perdedor {name[1:]}'
    return name


def _get_headers():
    api_key = settings.RAPID_API_KEY
    if not api_key:
        raise ValueError('RAPID_API_KEY não encontrada nas configurações.')
    return {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'sofascore6.p.rapidapi.com',
        'Content-Type': 'application/json',
    }


def _parse_placar(score_str):
    if not score_str:
        return None
    try:
        return int(score_str.split()[0])
    except (ValueError, IndexError):
        return None


def _buscar_cup_trees(headers):
    season_id = settings.SOFASCORE_SEASON_ID
    tournament_id = settings.SOFASCORE_TOURNAMENT_ID

    url = f'{BASE_URL}/v1/unique-tournament/season/cup-trees'
    params = {
        'season_id': season_id,
        'unique_tournament_id': tournament_id,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f'Erro ao buscar cup-trees: {e}')
        return None
    except ValueError:
        logger.error('A API cup-trees não retornou um JSON válido.')
        return None



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

    partidas_por_id = {p.id_api: p for p in partidas}

    cup_trees_data = _buscar_cup_trees(headers)

    blocos_por_match_id = {}
    if cup_trees_data:
        trees = cup_trees_data if isinstance(cup_trees_data, list) else [cup_trees_data]
        for tree in trees:
            for rnd in tree.get('rounds', []):
                for block in rnd.get('blocks', []):
                    match_id = block.get('matchId')
                    if match_id:
                        blocos_por_match_id[match_id] = block

    partidas_atualizadas = []
    partidas_notificaveis = []

    for partida in partidas:
        block = blocos_por_match_id.get(partida.id_api)

        if not block:
            logger.warning(f'Partida {partida.id_api} não encontrada nos dados do cup-trees.')
            continue

        old_placar_1 = partida.placar_1
        old_placar_2 = partida.placar_2
        old_status = partida.status

        partida.placar_1 = _parse_placar(block.get('homeTeamScore'))
        partida.placar_2 = _parse_placar(block.get('awayTeamScore'))

        is_finished = block.get('finished', False)
        if is_finished:
            partida.status = Partida.Status.FINALIZADA
            partida.tempo = 'Encerrado'
        elif partida.placar_1 is not None and partida.placar_2 is not None:
            if partida.status == Partida.Status.NAO_INICIADA and partida.data <= agora:
                partida.status = Partida.Status.EM_ANDAMENTO

        if partida.status in (Partida.Status.EM_ANDAMENTO, Partida.Status.FINALIZADA):
            try:
                atualizar_incidentes.apply_async(args=[partida.id_api], retry=False)
            except Exception as e:
                logger.warning(f'Celery offline, pulando incidentes em background para {partida.id_api}: {e}')

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
        
        partidas_finalizadas = [p for p in partidas_atualizadas if p.status == Partida.Status.FINALIZADA]
        if partidas_finalizadas:
            try:
                from chat.models import Sala
                Sala.objects.filter(partida__in=partidas_finalizadas).update(status=Sala.Status.FECHADA)
            except Exception as e:
                logger.error(f'Erro ao fechar salas das partidas finalizadas no bulk update: {e}')

        if partidas_notificaveis:
            try:
                from notificacao.signals import criar_notificacoes_para_partidas
                criar_notificacoes_para_partidas(partidas_notificaveis)
            except Exception as e:
                logger.error(f'Erro ao disparar notificações de partidas atualizadas: {e}')

    return f'{len(partidas_atualizadas)} partida(s) atualizada(s).'


@shared_task()
def importar_partidas():
    headers = _get_headers()

    logger.info('Buscando partidas via cup-trees...')
    cup_trees_data = _buscar_cup_trees(headers)

    if not cup_trees_data:
        logger.error('Não foi possível obter dados do cup-trees.')
        return 'Erro ao buscar dados do cup-trees.'

    trees = cup_trees_data if isinstance(cup_trees_data, list) else [cup_trees_data]

    total_criadas = 0
    total_atualizadas = 0

    for tree in trees:
        rounds = tree.get('rounds', [])

        for round_index, rnd in enumerate(rounds, start=1):
            fase_original = rnd.get('description', f'Fase {round_index}')
            fase = FASE_TRADUCAO.get(fase_original, fase_original)
            blocks = rnd.get('blocks', [])

            logger.info(f'Processando fase: {fase} ({len(blocks)} partidas)...')

            for block in blocks:
                try:
                    match_id = block.get('matchId')
                    if not match_id:
                        continue

                    participants = block.get('participants', [])
                    if len(participants) < 2:
                        logger.warning(
                            f'Partida {match_id} com menos de 2 participantes, ignorando.'
                        )
                        continue

                    name_1 = participants[0].get('team', {}).get('name', 'Desconhecido')
                    name_2 = participants[1].get('team', {}).get('name', 'Desconhecido')

                    time_1 = _traduzir_time(name_1)
                    time_2 = _traduzir_time(name_2)

                    is_finished = block.get('finished', False)
                    placar_1 = _parse_placar(block.get('homeTeamScore'))
                    placar_2 = _parse_placar(block.get('awayTeamScore'))

                    status = Partida.Status.FINALIZADA if is_finished else Partida.Status.NAO_INICIADA
                    tempo = 'Encerrado' if is_finished else None
                    data_partida = dj_timezone.now()

                    partida_existente = Partida.objects.filter(id_api=match_id).first()
                    estatisticas_atuais = (
                        partida_existente.estatisticas_finais if partida_existente else None
                    )

                    if partida_existente:
                        data_partida = partida_existente.data

                    _, created = Partida.objects.update_or_create(
                        id_api=match_id,
                        defaults={
                            'time_1': time_1,
                            'time_2': time_2,
                            'placar_1': placar_1,
                            'placar_2': placar_2,
                            'data': data_partida,
                            'status': status,
                            'tempo': tempo,
                            'estatisticas_finais': estatisticas_atuais,
                            'fase': fase,
                        },
                    )

                    if status in (Partida.Status.EM_ANDAMENTO, Partida.Status.FINALIZADA):
                        if not (status == Partida.Status.FINALIZADA and estatisticas_atuais):
                            try:
                                atualizar_incidentes.apply_async(args=[match_id], retry=False)
                            except Exception as e:
                                logger.warning(f'Celery offline, pulando incidentes em background para {match_id}: {e}')

                    if created:
                        total_criadas += 1
                    else:
                        total_atualizadas += 1

                    logger.info(
                        f'  {time_1} x {time_2} '
                        f'(ID: {match_id}, Fase: {fase}) - '
                        f'{"criada" if created else "atualizada"}'
                    )

                except (KeyError, TypeError, ValueError) as e:
                    logger.warning(
                        f'Erro ao processar partida {block.get("matchId", "?")}: {e}'
                    )

    resultado = f'{total_criadas} criadas, {total_atualizadas} atualizadas.'
    logger.info(f'Importação concluída! {resultado}')
    return resultado