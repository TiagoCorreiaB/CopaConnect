from django.db import models, transaction
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=11, unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'telefone']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        with transaction.atomic():
            super().save(*args, **kwargs)
            
            if is_new:
                Perfil.objects.create(
                    usuario=self,
                    nome=self.first_name
                )

class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)
    apelido = models.CharField(max_length=30)
    descricao = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'Perfil de {self.nome}'