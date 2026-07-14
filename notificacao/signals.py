from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from usuarios.models import Usuario, Amizade
from bolao.models import Bolao
from partidas.models import Partida
from notificacao.models import Notificacao

@receiver(post_save, sender=Amizade)
def criar_notificacao_pedido_amizade(sender, instance, created, **kwargs):
    if created and instance.status == Amizade.Status.PENDENTE:
        Notificacao.objects.create(
            usuario=instance.amigo,
            titulo="Novo pedido de amizade",
            mensagem=f"{instance.usuario.first_name or instance.usuario.username} enviou um pedido de amizade para você.",
            url=f"/api/copaconnect/v1/amizades/{instance.id}/"
        )
    elif not created and instance.status == Amizade.Status.ACEITO:
        Notificacao.objects.create(
            usuario=instance.usuario,
            titulo="Pedido de amizade aceito",
            mensagem=f"{instance.amigo.first_name or instance.amigo.username} aceitou o seu pedido de amizade.",
            url=f"/api/copaconnect/v1/perfis/{instance.amigo.perfil.id}/" if hasattr(instance.amigo, 'perfil') else None
        )

@receiver(m2m_changed, sender=Bolao.usuarios.through)
def criar_notificacao_adicionado_bolao(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            if user_id == instance.dono_id:
                continue
            try:
                user = Usuario.objects.get(pk=user_id)
                Notificacao.objects.create(
                    usuario=user,
                    titulo="Adicionado a um bolão",
                    mensagem=f"Você foi adicionado ao bolão '{instance.nome}' por {instance.dono.first_name or instance.dono.username}.",
                    url=f"/api/copaconnect/v1/boloes/{instance.id}/"
                )
            except Usuario.DoesNotExist:
                pass

@receiver(pre_save, sender=Partida)
def guardar_valores_anteriores_partida(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Partida.objects.get(pk=instance.pk)
            instance._old_placar_1 = old_instance.placar_1
            instance._old_placar_2 = old_instance.placar_2
            instance._old_status = old_instance.status
        except Partida.DoesNotExist:
            pass

def criar_notificacoes_para_partidas(partidas):
    notificacoes_para_criar = []
    
    for instance in partidas:
        boloes = Bolao.objects.filter(partida=instance).distinct()
        if not boloes.exists():
            continue
            
        status_display = instance.get_status_display()
        placar_str = f"{instance.placar_1 if instance.placar_1 is not None else 0} x {instance.placar_2 if instance.placar_2 is not None else 0}"
        
        users_to_notify = set()
        for bolao in boloes:
            users_to_notify.update(bolao.usuarios.all())
            users_to_notify.add(bolao.dono)
            
        for user in users_to_notify:
            notificacoes_para_criar.append(
                Notificacao(
                    usuario=user,
                    titulo=f"Atualização da partida: {instance.time_1} x {instance.time_2}",
                    mensagem=f"A partida '{instance.time_1} x {instance.time_2}' foi atualizada. Status: {status_display}. Placar: {placar_str}.",
                    url=f"/api/copaconnect/v1/partidas/{instance.id}/"
                )
            )
            
    if notificacoes_para_criar:
        Notificacao.objects.bulk_create(notificacoes_para_criar)

@receiver(post_save, sender=Partida)
def criar_notificacao_alteracao_partida(sender, instance, created, **kwargs):
    if not created:
        old_placar_1 = getattr(instance, '_old_placar_1', None)
        old_placar_2 = getattr(instance, '_old_placar_2', None)
        old_status = getattr(instance, '_old_status', None)
        
        changed = (
            old_placar_1 != instance.placar_1 or
            old_placar_2 != instance.placar_2 or
            old_status != instance.status
        )
        if changed:
            criar_notificacoes_para_partidas([instance])