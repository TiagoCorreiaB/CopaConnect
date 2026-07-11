from celery import shared_task
from gemini_api.client import get_descricao_bolao
from .models import Bolao

@shared_task
def gerar_descricao_task(bolao_id):
    bolao = Bolao.objects.get(id=bolao_id)
    partida = bolao.partida
        
    descricao_ia = get_descricao_bolao(
        time_1=partida.time_1,
        time_2=partida.time_2,
        data=partida.data,
        fase=partida.fase
    )
    
    bolao.descricao = descricao_ia
    bolao.save(update_fields=['descricao'])