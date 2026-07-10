from .models import Bolao, Palpite
from .serializers import BolaoWriteModelSerializer, BolaoReadModelSerializer, PalpiteModelSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets


class BolaoModelViewSet(viewsets.ModelViewSet):
    queryset = Bolao.objects.all()
    filterset_fields = ['status', 'dono', 'partida']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return BolaoReadModelSerializer
        
        return BolaoWriteModelSerializer

    def perform_create(self, serializer):
        bolao = serializer.save(dono=self.request.user)
        bolao.usuarios.add(self.request.user)

    def perform_update(self, serializer):
        if self.get_object().dono != self.request.user:
            raise PermissionDenied("Apenas o dono pode editar este bolão.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.dono != self.request.user:
            raise PermissionDenied("Apenas o dono pode deletar este bolão.")
        instance.delete()

class PalpiteModelViewSet(viewsets.ModelViewSet):
    queryset = Palpite.objects.all()
    filterset_fields = ['usuario', 'bolao']
    serializer_class = PalpiteModelSerializer