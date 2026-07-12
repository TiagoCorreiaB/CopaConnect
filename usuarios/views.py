from rest_framework import viewsets, mixins
from .models import Usuario, Perfil
from .serializers import UsuarioSerializer, PerfilSerializer

class UsuarioModelViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class PerfilReadUpdateModelViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer