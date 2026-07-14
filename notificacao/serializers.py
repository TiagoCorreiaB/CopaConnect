from rest_framework import serializers
from .models import Notificacao
from usuarios.serializers import UsuarioReadModelSerializer

class NotificacaoModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id','titulo','mensagem','url','lida','data_criacao','usuario']
    
    usuario = UsuarioReadModelSerializer(read_only=True)