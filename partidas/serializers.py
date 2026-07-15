from .models import Partida
from rest_framework import serializers

class PartidaModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partida
        fields = ['id','time_1','time_2','placar_1','placar_2','data','status','tempo','fase','estatisticas_finais']