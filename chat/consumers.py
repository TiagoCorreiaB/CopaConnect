from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin, action
from djangochannelsrestframework.mixins import ListModelMixin
from .models import Sala, Comentario
from usuarios.models import Usuario
from .serializers import ComentarioReadModelSerializer, SalaModelSerializer

class SalaConsumer(ListModelMixin, ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    serializer_class = SalaModelSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        from django.db.models import Count, Prefetch
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
    
    @action()
    async def entrar(self, pk, request_id, **kwargs):
        sala = await database_sync_to_async(self.get_object)(pk=pk)
        await self.subscribe_instance(request_id=request_id, pk=sala.pk)
        await self.atividade_comentario.subscribe(sala=pk, request_id=request_id)
        if self.scope['user'].is_authenticated:
            await self.adicionar(sala)

    @action()
    async def sair(self, pk, **kwargs):
        sala = await database_sync_to_async(self.get_object)(pk=pk)
        if self.scope['user'].is_authenticated:
            await self.remover(sala)
        await self.unsubscribe_instance(pk=sala.pk)
        await self.atividade_comentario.unsubscribe(sala=sala.pk)

    @database_sync_to_async
    def adicionar(self, sala: Sala):
        usuario = Usuario.objects.get(pk=self.scope['user'].pk)
        sala.usuarios.add(usuario)

    @database_sync_to_async
    def remover(self, sala: Sala):
        usuario = Usuario.objects.get(pk=self.scope['user'].pk)
        sala.usuarios.remove(usuario)

    @action()
    async def criar_comentario(self, comentario, sala, **kwargs):
        if not self.scope['user'].is_authenticated:
            return

        sala: Sala = await database_sync_to_async(self.get_object)(pk=sala)

        if sala.status == Sala.Status.FECHADA:
            await self.send_json({
                'erro': 'Não é possível enviar comentários em uma sala fechada.'
            })
            return

        usuario = await database_sync_to_async(Usuario.objects.get)(pk=self.scope['user'].pk)

        pertence = await database_sync_to_async(sala.usuarios.filter(pk=usuario.pk).exists)()
        if not pertence:
            await self.send_json({
                'erro': 'Você precisa estar na sala para enviar comentários.'
            })
            return

        await database_sync_to_async(Comentario.objects.create)(
            sala=sala,
            usuario=usuario,
            texto=comentario
        )

    @model_observer(Comentario)
    async def atividade_comentario(
        self,
        comentario,
        observer=None,
        subscribing_request_ids=[],
        **kwargs
    ):
        for request_id in subscribing_request_ids:
            texto_comentario = dict(request_id=request_id)
            texto_comentario.update(comentario)
            await self.send_json(texto_comentario)

    @atividade_comentario.groups_for_signal
    def atividade_comentario(self, instance: Comentario, **kwargs):
        yield f'sala__{instance.sala_id}'

    @atividade_comentario.groups_for_consumer
    def atividade_comentario(self, sala=None, **kwargs):
        if sala is not None:
            yield f'sala__{sala}'

    @atividade_comentario.serializer
    def atividade_comentario(self, comentario: Comentario, acao, **kwargs):
        return dict(
            dados=ComentarioReadModelSerializer(comentario).data,
            acao=acao.value,
            pk=comentario.pk
        )