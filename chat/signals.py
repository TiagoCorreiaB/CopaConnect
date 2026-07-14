from django.db.models.signals import post_save
from django.dispatch import receiver
from partidas.models import Partida
from chat.models import Sala

@receiver(post_save, sender=Partida)
def gerenciar_sala_partida(sender, instance, created, **kwargs):
    if created:
        Sala.objects.get_or_create(
            partida=instance,
            defaults={
                'nome': f"{instance.time_1} x {instance.time_2}",
                'status': Sala.Status.ABERTA
            }
        )
    else:
        if instance.status == Partida.Status.FINALIZADA:
            Sala.objects.filter(partida=instance).update(status=Sala.Status.FECHADA)
