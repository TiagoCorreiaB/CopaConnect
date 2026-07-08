from rest_framework import serializers
from .models import Bolao, Palpite

class BolaoModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bolao
        fields = '__all__'

class PalpiteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Palpite
        fields = '__all__'