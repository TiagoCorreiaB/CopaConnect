from .models import Sala, Comentario
from rest_framework import serializers
from usuarios.serializers import UsuarioSerializer

class ComentarioSerializer(serializers.ModelSerializer):
    data_envio_formatada = serializers.SerializerMethodField()
    usuario = UsuarioSerializer()

    class Meta:
        model = Comentario
        exclude = []
        depth = 1

    def get_data_envio_formatada(self, obj:Comentario):
        return obj.data_envio.strftime('%H:%M')
    
    
class SalaSerializer(serializers.ModelSerializer):
    ultimo_comentario = serializers.SerializerMethodField()
    comentarios = ComentarioSerializer(many=True, read_only=True)

    class Meta:
        model = Sala
        fields = ["id", "nome", "comentarios", "usuarios", "ultimo_comentario"]
        depth = 1
        read_only_fields = ["comentarios", "ultimo_comentario"]

    def get_ultimo_comentario(self, obj:Sala):
        return ComentarioSerializer(obj.comentarios.order_by('data_envio').last()).data