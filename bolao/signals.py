from django.db.models.signals import post_save
from django.dispatch import receiver
from partidas.models import Partida
from bolao.models import Bolao, Palpite

def calcular_pontuacao_palpite(placar_real_1, placar_real_2, palpite_1, palpite_2):
    if palpite_1 == placar_real_1 and palpite_2 == placar_real_2:
        return 25
    
    real_vencedor = 1 if placar_real_1 > placar_real_2 else (2 if placar_real_2 > placar_real_1 else 0)
    palpite_vencedor = 1 if palpite_1 > palpite_2 else (2 if palpite_2 > palpite_1 else 0)

    acertou_vencedor_ou_empate = (real_vencedor == palpite_vencedor)

    real_saldo = placar_real_1 - placar_real_2
    palpite_saldo = palpite_1 - palpite_2
    acertou_saldo = (real_saldo == palpite_saldo)

    acertou_gols_time1 = (palpite_1 == placar_real_1)
    acertou_gols_time2 = (palpite_2 == placar_real_2)

    if acertou_vencedor_ou_empate and acertou_saldo:
        return 18

    if acertou_vencedor_ou_empate and (acertou_gols_time1 or acertou_gols_time2):
        return 15

    if acertou_vencedor_ou_empate:
        return 10

    if acertou_gols_time1 or acertou_gols_time2:
        return 4

    return 0


def atualizar_pontos_e_vencedores_para_partidas(partidas):
    partidas_finalizadas = [p for p in partidas if p.status == Partida.Status.FINALIZADA]
    if not partidas_finalizadas:
        return

    palpites_para_atualizar = []
    palpites = Palpite.objects.filter(bolao__partida__in=partidas_finalizadas).select_related('bolao__partida')

    for palpite in palpites:
        partida = palpite.bolao.partida
        if partida.placar_1 is not None and partida.placar_2 is not None:
            nova_pontuacao = calcular_pontuacao_palpite(
                placar_real_1=partida.placar_1,
                placar_real_2=partida.placar_2,
                palpite_1=palpite.placar_1,
                palpite_2=palpite.placar_2
            )
            if palpite.pontuacao != nova_pontuacao:
                palpite.pontuacao = nova_pontuacao
                palpites_para_atualizar.append(palpite)

    if palpites_para_atualizar:
        Palpite.objects.bulk_update(palpites_para_atualizar, ['pontuacao'])

    boloes_para_atualizar = []
    boloes = Bolao.objects.filter(partida__in=partidas_finalizadas).exclude(status=Bolao.Status.FINALIZADO)

    for bolao in boloes:
        melhor_palpite = bolao.palpites.order_by('-pontuacao').first()
        if melhor_palpite and melhor_palpite.pontuacao is not None:
            bolao.vencedor = melhor_palpite.dono
        bolao.status = Bolao.Status.FINALIZADO
        boloes_para_atualizar.append(bolao)

    if boloes_para_atualizar:
        Bolao.objects.bulk_update(boloes_para_atualizar, ['status', 'vencedor'])


@receiver(post_save, sender=Partida)
def gerenciar_pontuacao_palpites_sinal(sender, instance, created, **kwargs):
    if not created and instance.status == Partida.Status.FINALIZADA:
        atualizar_pontos_e_vencedores_para_partidas([instance])
