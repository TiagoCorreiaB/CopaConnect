from django.utils import timezone
from rest_framework import serializers
from .models import Bolao, Palpite
from usuarios.serializers import UsuarioSerializer
from partidas.serializers import PartidaSerializer
from partidas.models import Partida
from .tasks import gerar_descricao_task

class BolaoWriteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bolao
        fields = '__all__'
        read_only_fields = ['dono','usuarios']

    def validate_partida(self, value):
        if value.status != Partida.Status.NAO_INICIADA:
            raise serializers.ValidationError(
                'A partida não está mais com o status "Não iniciada".'
            )

        if value.data < timezone.now():
            raise serializers.ValidationError(
                'O horário previsto para a partida já passou'
            )

        return value
    
    def validate_vencedor(self, value):
        if self.instance is None and value is not None:
            raise serializers.ValidationError(
                'Não é possível definir um vencedor no momento da criação do bolão.'
            )
        return value
    
    def validate_status(self, value):
        if self.instance is None and value == Bolao.Status.FINALIZADO:
            raise serializers.ValidationError(
                'Um bolão não pode ser criado já com o status finalizado.'
            )
        return value

    def create(self, validated_data):
        descricao = validated_data.get('descricao', '')

        if not descricao:
            validated_data['descricao'] = 'Gerando descrição com IA.'
            bolao = super().create(validated_data)
            gerar_descricao_task.delay(bolao.id)
            return bolao
        
        return super().create(validated_data)
    
class BolaoReadModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bolao
        fields = '__all__'

    quantidade_usuarios = serializers.SerializerMethodField(read_only=True)
    dono = UsuarioSerializer(read_only=True)
    vencedor = UsuarioSerializer(read_only=True)
    partida = PartidaSerializer(read_only=True)
    usuarios = UsuarioSerializer(read_only=True, many=True)
    
    def get_quantidade_usuarios(self, obj):
        return obj.usuarios.count()

class PalpiteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Palpite
        fields = '__all__'