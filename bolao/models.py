from django.db import models
from usuarios.models import Usuario
from partidas.models import Partida

class Bolao(models.Model):
    class Status(models.TextChoices):
        INICIADO = 'IN','Iniciado'
        FINALIZADO = 'FI', 'Finalizado'
        
    nome = models.CharField(max_length=50)
    descricao = models.TextField()
    partida = models.ForeignKey(Partida, related_name='boloes', on_delete=models.CASCADE)
    vencedor = models.ForeignKey(
        Usuario,
        related_name='boloes_vencidos',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        verbose_name='Status',
        default=Status.INICIADO
    )
    usuarios = models.ManyToManyField(Usuario, related_name='boloes', blank=True)

    class Meta:
        verbose_name = 'Bolão'
        verbose_name_plural = 'Bolões'

    def __str__(self):
        return self.nome
    
class Palpite(models.Model):
    placar_1 = models.IntegerField()
    placar_2 = models.IntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, related_name='palpites', on_delete=models.CASCADE)
    bolao = models.ForeignKey(Bolao, related_name='palpites', on_delete=models.CASCADE)
    pontuacao = models.IntegerField(null=True, blank=True)
    valor_pontuacao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Palpite'
        verbose_name_plural = 'Palpites'

    def __str__(self):
        return f'{self.placar_1}  X  {self.placar_2}'