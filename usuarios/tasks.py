import logging
from datetime import datetime
from celery import shared_task
from .models import Usuario

logger = logging.getLogger(__name__)

@shared_task
def verificar_e_definir_offline(usuario_id, tempo_desconexao_str):
    try:
        tempo_desconexao = datetime.fromisoformat(tempo_desconexao_str)
        usuario = Usuario.objects.get(pk=usuario_id)
        if usuario.ultima_atividade == tempo_desconexao:
            usuario.online = False
            usuario.save(update_fields=['online'])
            logger.info(f"Usuario {usuario.username} definido como offline apos 2 minutos de inatividade.")
    except Exception as e:
        logger.error(f"Erro ao definir usuario {usuario_id} offline: {e}")