from django.db import models

class Partida(models.Model):
    class Status(models.TextChoices):
        NAO_INICIADA = 'NI', 'Não iniciada'
        EM_ANDAMENTO = 'EA', 'Em andamento'
        FINALIZADA = 'FI', 'Finalizada'
        ADIADA = 'AD', 'Adiada'
        CANCELADA = 'CA', 'Cancelada'

    id_api = models.IntegerField(unique=True)
    time_1 = models.CharField(max_length=100)
    time_2 = models.CharField(max_length=100)
    placar_1 = models.IntegerField(null=True, blank=True)
    placar_2 = models.IntegerField(null=True, blank=True)
    data = models.DateTimeField()
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        verbose_name='Status',
        default=Status.NAO_INICIADA
    )
    tempo = models.CharField(max_length=10, null=True, blank=True)
    fase = models.CharField(max_length=50)
    estatisticas_finais = models.JSONField(null=True, blank=True)