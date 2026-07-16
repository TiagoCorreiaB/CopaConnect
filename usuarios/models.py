
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=11, unique=True)
    online = models.BooleanField(default=False)
    ultima_atividade = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'telefone']

class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)
    apelido = models.CharField(max_length=30)
    descricao = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'Perfil de {self.apelido}'
    
class Amizade(models.Model):
    class Status(models.TextChoices):
        ACEITO = 'AC', 'Aceito'
        PENDENTE = 'PE', 'Pendente'
        BLOQUEADO = 'BL', 'Bloqueado'

    usuario = models.ForeignKey(Usuario, related_name='amizades_iniciadas', on_delete=models.CASCADE)                            
    amigo = models.ForeignKey(Usuario, related_name='amizades_recebidas', on_delete=models.CASCADE)                              
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        verbose_name='Status',
        default=Status.PENDENTE
    )

    class Meta:                                
        unique_together = ('usuario', 'amigo')