import json

from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin, action

from .models import Sala, Comentario
from usuarios.models import Usuario
from .serializers import ComentarioSerializer, SalaSerializer
from usuarios.serializers import UsuarioSerializer

class SalaConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    lookup_field = "id"