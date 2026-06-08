from django.db import models
from usuarios.models import Usuario

class Sala(models.Model):
    class Status(models.TextChoices):
        ABERTA = 'AB','Aberta'
        FECHADA = 'FE', 'Fechada'

    nome = models.CharField(max_length=100)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        verbose_name='Status',
        default=Status.ABERTA
    )
    usuarios = models.ManyToManyField(Usuario, related_name='salas', blank=True)

    def __str__(self):
        return f'Sala {self.nome}'
    
class Comentario(models.Model):
    sala = models.ForeignKey('chat.Sala', on_delete=models.CASCADE, related_name='comentarios')
    texto = models.TextField(max_length=200)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='comentarios')
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario}: {self.texto}'