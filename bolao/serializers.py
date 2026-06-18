from rest_framework import serializers
from .models import Bolao, Palpite, Pontuacao
from usuarios.serializers import UsuarioSerializer
from partidas.serializers import PartidaSerializer

class BolaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bolao
        fields = '__all__'


class PalpiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Palpite
        fields = '__all__'

class PontuacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pontuacao
        fields = '__all__'