from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notificacao
from .serializers import NotificacaoModelSerializer

class NotificacaoReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificacaoModelSerializer
    filterset_fields = ['titulo']

    def get_queryset(self):
        return Notificacao.objects.filter(usuario=self.request.user)

    @action(detail=True, methods=['post'], url_path='marcar-como-lida')
    def marcar_como_lida(self, request, pk=None):
        notificacao = self.get_object()
        notificacao.lida = True
        notificacao.save(update_fields=['lida'])
        return Response({'status': 'Notificação marcada como lida.'})