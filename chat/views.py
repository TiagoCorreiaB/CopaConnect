from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import Sala, Comentario
from .serializers import SalaModelSerializer, ComentarioWriteModelSerializer, ComentarioReadModelSerializer

class SalaReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaModelSerializer
    filterset_fields = ['status']

class ComentarioModelViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all().order_by('data_envio')
    filterset_fields = ['sala']
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ComentarioReadModelSerializer
        
        return ComentarioWriteModelSerializer
    
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        if self.get_object().usuario != self.request.user:
            raise PermissionDenied('Apenas o usuário pode editar o comentário.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.usuario != self.request.user:
            raise PermissionDenied('Apenas o usuário pode apagar o comentário.')
        instance.delete()