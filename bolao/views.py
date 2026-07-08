from .models import Bolao, Palpite
from .serializers import BolaoModelSerializer, PalpiteModelSerializer
from rest_framework import viewsets


class BolaoModelViewSet(viewsets.ModelViewSet):
    queryset = Bolao.objects.all()
    filterset_fields = ['status', 'vencedor', 'partida']
    serializer_class = BolaoModelSerializer

class PalpiteModelViewSet(viewsets.ModelViewSet):
    queryset = Palpite.objects.all()
    filterset_fields = ['usuario', 'bolao']
    serializer_class = PalpiteModelSerializer