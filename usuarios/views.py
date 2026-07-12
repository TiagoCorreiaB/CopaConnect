from rest_framework import viewsets, mixins
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Usuario, Perfil
from .serializers import UsuarioReadModelSerializer, UsuarioWriteModelSerializer, PerfilModelSerializer

class UsuarioFilter(filters.FilterSet):
    nome = filters.CharFilter(method='filter_por_nome')

    class Meta:
        model = Usuario
        fields = ['username'] 

    def filter_por_nome(self, queryset, name, value):
        return queryset.filter(Q(first_name__icontains=value)|Q(last_name__icontains=value))


class UsuarioModelViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    filterset_class =  UsuarioFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UsuarioReadModelSerializer
        
        return UsuarioWriteModelSerializer
    
    def perform_update(self, serializer):
        if self.get_object() != self.request.user:
            raise PermissionDenied('Apenas o usuário pode editar.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance != self.request.user:
            raise PermissionDenied('Apenas o usuário pode apagar.')
        instance.delete()

class PerfilReadUpdateModelViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    queryset = Perfil.objects.all()
    serializer_class = PerfilModelSerializer