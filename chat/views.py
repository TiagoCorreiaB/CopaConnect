from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import CursorPagination
from .models import Sala, Comentario
from .serializers import SalaModelSerializer, ComentarioWriteModelSerializer, ComentarioReadModelSerializer
from django.db.models import Count, Prefetch

class ComentarioCursorPagination(CursorPagination):
    page_size = 50
    ordering = '-data_envio'

class SalaReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SalaModelSerializer
    filterset_fields = ['status']

    def get_queryset(self):
        return Sala.objects.select_related('partida').prefetch_related(
            'usuarios',
            Prefetch(
                'comentarios',
                queryset=Comentario.objects.select_related('usuario').order_by('-data_envio'),
                to_attr='ultimo_comentario_prefetched'
            )
        ).annotate(
            quantidade_usuarios_count=Count('usuarios', distinct=True)
        )

class ComentarioModelViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    pagination_class = ComentarioCursorPagination
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