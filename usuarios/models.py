from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=11, unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'telefone']

class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)
    nome = models.CharField(max_length=30)
    descricao = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'Perfil de {self.nome}'