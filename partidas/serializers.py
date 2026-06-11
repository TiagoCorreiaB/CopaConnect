from .models import Partida
from rest_framework import serializers

class PartidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partida
        exclude = ['id_api']