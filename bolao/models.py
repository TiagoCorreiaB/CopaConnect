from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from usuarios.models import Usuario
from partidas.models import Partida

class Bolao(models.Model):
    class Status(models.TextChoices):
        INICIADO = 'IN','Iniciado'
        FINALIZADO = 'FI', 'Finalizado'
        
    nome = models.CharField(max_length=50)
    descricao = models.TextField(blank=True, null=True)
    partida = models.ForeignKey(
        Partida,
        related_name='boloes',
        on_delete=models.CASCADE
    )
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
    usuarios = models.ManyToManyField(
        Usuario,
        related_name='boloes',
        blank=True
    )
    dono = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='boloes_criados'
    )

    class Meta:
        verbose_name = 'Bolão'
        verbose_name_plural = 'Bolões'

    def __str__(self):
        return self.nome
    
class Palpite(models.Model):
    placar_1 = models.IntegerField(
        validators=[
            MinValueValidator(0, 'O valor do placar não pode ser inferior a 0'),
            MaxValueValidator(99, 'O valor do placar não pode ser superior a 99')
        ]
    )
    placar_2 = models.IntegerField(
        validators=[
            MinValueValidator(0, 'O valor do placar não pode ser inferior a 0'),
            MaxValueValidator(99, 'O valor do placar não pode ser superior a 99')
        ]
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(1, 'O valor do palpite não pode ser inferior a 1'),
        ]
    )
    data = models.DateTimeField(auto_now_add=True)
    dono = models.ForeignKey(Usuario, related_name='palpites', on_delete=models.CASCADE)
    bolao = models.ForeignKey(Bolao, related_name='palpites', on_delete=models.CASCADE)
    pontuacao = models.IntegerField(null=True, blank=True)
    valor_pontuacao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Palpite'
        verbose_name_plural = 'Palpites'

    def __str__(self):
        return f'{self.placar_1}  X  {self.placar_2}'