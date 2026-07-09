from .models import Bolao, Palpite
from .serializers import BolaoModelSerializer, PalpiteModelSerializer
from rest_framework import viewsets


class BolaoModelViewSet(viewsets.ModelViewSet):
    queryset = Bolao.objects.all()
    filterset_fields = ['status', 'vencedor', 'partida']
    serializer_class = BolaoModelSerializer

    def perform_create(self, serializer):
        bolao = serializer.save(dono=self.request.user)
        bolao.usuarios.add(self.request.user)

class PalpiteModelViewSet(viewsets.ModelViewSet):
    queryset = Palpite.objects.all()
    filterset_fields = ['usuario', 'bolao']
    serializer_class = PalpiteModelSerializer