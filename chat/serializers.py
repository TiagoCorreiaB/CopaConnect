from rest_framework import serializers
from .models import Sala, Comentario
from usuarios.serializers import UsuarioReadModelSerializer
from partidas.serializers import PartidaModelSerializer

class ComentarioWriteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comentario
        fields = ['id', 'sala', 'usuario', 'texto', 'data_envio']
        read_only_fields = ['usuario', 'data_envio']

    def validate_sala(self, value):
        if value.status == Sala.Status.FECHADA:
            raise serializers.ValidationError(
                'Não é possível enviar comentários em uma sala fechada.'
            )

        request = self.context.get('request')
        if request and not value.usuarios.filter(pk=request.user.pk).exists():
            raise serializers.ValidationError(
                'Você precisa estar na sala para enviar comentários.'
            )

        return value

class ComentarioReadModelSerializer(serializers.ModelSerializer):
    usuario = UsuarioReadModelSerializer(read_only=True)
    data_envio_formatada = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comentario
        fields = ['id', 'sala', 'usuario', 'texto', 'data_envio', 'data_envio_formatada']

    def get_data_envio_formatada(self, obj: Comentario):
        from django.utils import timezone
        return timezone.localtime(obj.data_envio).strftime('%H:%M')

class SalaModelSerializer(serializers.ModelSerializer):
    partida = PartidaModelSerializer(read_only=True)
    usuarios = UsuarioReadModelSerializer(read_only=True, many=True)
    quantidade_usuarios = serializers.SerializerMethodField(read_only=True)
    ultimo_comentario = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Sala
        fields = [
            'id', 'nome', 'status', 'partida',
            'usuarios', 'quantidade_usuarios', 'ultimo_comentario',
        ]

    def get_quantidade_usuarios(self, obj: Sala):
        if hasattr(obj, 'quantidade_usuarios_count'):
            return obj.quantidade_usuarios_count
        return obj.usuarios.count()

    def get_ultimo_comentario(self, obj: Sala):
        if hasattr(obj, 'ultimo_comentario_prefetched'):
            ultimo = obj.ultimo_comentario_prefetched[0] if obj.ultimo_comentario_prefetched else None
        else:
            ultimo = obj.comentarios.order_by('data_envio').last()
            
        if ultimo is None:
            return None
        return ComentarioReadModelSerializer(ultimo, context=self.context).data