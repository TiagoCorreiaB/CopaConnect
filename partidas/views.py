from .models import Partida
from .serializers import PartidaSerializer
from rest_framework import viewsets

class PartidaViewSet(viewsets.ModelViewSet):
    queryset = Partida.objects.all()
    serializer_class = PartidaSerializer