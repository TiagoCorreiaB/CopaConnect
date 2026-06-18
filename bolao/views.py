from .models import Bolao, Palpite, Pontuacao
from .serializers import BolaoSerializer, PalpiteSerializer, PontuacaoSerializer
from rest_framework import viewsets


class BolaoViewSet(viewsets.ModelViewSet):
    queryset = Bolao.objects.all()
    filterset_fields = ['status', 'vencedor', 'partida']
    serializer_class = BolaoSerializer

class PalpiteViewSet(viewsets.ModelViewSet):
    queryset = Palpite.objects.all()
    filterset_fields = ['usuario', 'bolao']
    serializer_class = PalpiteSerializer

class PontuacaoViewSet(viewsets.ModelViewSet):
    queryset = Pontuacao.objects.all()
    filterset_fields = ['palpite']
    serializer_class = PontuacaoSerializer