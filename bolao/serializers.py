from django.utils import timezone
from rest_framework import serializers
from .models import Bolao, Palpite
from usuarios.serializers import UsuarioSerializer
from gemini_api.client import get_descricao_bolao

class BolaoModelSerializer(serializers.ModelSerializer):
    quantidade_usuarios = serializers.SerializerMethodField(read_only=True)
    dono = UsuarioSerializer(read_only=True)

    class Meta:
        model = Bolao
        fields = '__all__'

    def get_quantidade_usuarios(self, obj):
        return obj.usuarios.count()
    
    def validate_partida(self, value):
        if value.data < timezone.now():
            raise serializers.ValidationError(
                'A partida já aconteceu, então não é possível criar um bolão'
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
        partida = validated_data.get('partida')

        if not descricao:
            
            descricao_ia = get_descricao_bolao(
                time_1=partida.time_1,
                time_2=partida.time_2,
                data=partida.data,
                fase=partida.fase
            )
            
            validated_data['descricao'] = descricao_ia
        return super().create(validated_data)

class PalpiteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Palpite
        fields = '__all__'