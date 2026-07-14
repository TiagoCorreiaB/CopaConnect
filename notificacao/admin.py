from django.contrib import admin
from .models import Notificacao

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'usuario', 'lida', 'data_criacao']