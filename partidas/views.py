from .models import Partida
from .serializers import PartidaSerializer
from rest_framework import viewsets

class PartidaReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Partida.objects.all()
    serializer_class = PartidaSerializer