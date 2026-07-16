from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Usuario, Perfil, Amizade
from .serializers import UsuarioReadModelSerializer, UsuarioWriteModelSerializer, PerfilReadModelSerializer, PerfilWriteModelSerializer, AmizadeReadModelSerializer, AmizadeWriteModelSerializer

class UsuarioModelViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ['username', 'perfil__apelido']

    def get_permissions(self):
        if self.action == 'create':
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        return super().get_permissions()

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
    filterset_fields = ['usuario']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PerfilReadModelSerializer
        
        return PerfilWriteModelSerializer
    
    def perform_update(self, serializer):
        if self.get_object().usuario != self.request.user:
            raise PermissionDenied('Apenas o usuário pode editar.')
        serializer.save()

class AmizadeModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        usuario = self.request.user
        return Amizade.objects.filter(Q(usuario=usuario)|Q(amigo=usuario)).distinct()
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return AmizadeReadModelSerializer
        
        return AmizadeWriteModelSerializer
    
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        amizade = self.get_object()
        if self.request.user not in [amizade.usuario, amizade.amigo]:
            raise PermissionDenied('Você não tem permissão para alterar esta amizade.')
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user not in [instance.usuario, instance.amigo]:
            raise PermissionDenied('Você não tem permissão para apagar esta amizade.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def aceitar(self, request, pk=None):
        amizade = self.get_object()

        if amizade.amigo != request.user:
            raise PermissionDenied('Apenas o destinatário do convite pode aceitá-lo.')

        if amizade.status == Amizade.Status.ACEITO:
            return Response(
                {'detalhe': 'Este convite de amizade já foi aceito.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        amizade.status = Amizade.Status.ACEITO
        amizade.save()

        return Response(
            {'detalhe': 'Convite de amizade aceito com sucesso!'}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        amizade = self.get_object()

        if request.user not in [amizade.usuario, amizade.amigo]:
            raise PermissionDenied('Você não tem permissão para interagir com este convite.')

        amizade.delete()

        return Response(
            {'detalhe': 'Convite recusado/apagado com sucesso.'}, 
            status=status.HTTP_204_NO_CONTENT
        )