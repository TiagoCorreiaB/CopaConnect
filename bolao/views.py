from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Bolao, Palpite
from .serializers import BolaoWriteModelSerializer, BolaoReadModelSerializer, PalpiteWriteModelSerializer, PalpiteReadModelSerializer
from usuarios.models import Usuario

class BolaoModelViewSet(viewsets.ModelViewSet):
    filterset_fields = ['status', 'partida']

    def get_queryset(self):
        usuario = self.request.user
        return Bolao.objects.filter(Q(dono=usuario)|Q(usuarios=usuario)).distinct()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return BolaoReadModelSerializer
        
        return BolaoWriteModelSerializer

    def perform_create(self, serializer):
        bolao = serializer.save(dono=self.request.user)
        bolao.usuarios.add(self.request.user)

    def perform_update(self, serializer):
        if self.get_object().dono != self.request.user:
            raise PermissionDenied('Apenas o dono pode editar este bolão.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.dono != self.request.user:
            raise PermissionDenied('Apenas o dono pode deletar este bolão.')
        instance.delete()

    @action(detail=True, methods=['post'], url_path='adicionar')
    def adicionar_usuario(self, request, pk=None):
        bolao = self.get_object()
        
        if bolao.dono != request.user:
            return Response(
                {'detalhe': 'Apenas o dono pode adicionar participantes neste bolão.'},
                status=status.HTTP_403_FORBIDDEN
            )

        usuario_id = request.data.get('usuario_id')
        if not usuario_id:
            return Response(
                {'detalhe': 'O campo "usuario_id" é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = get_object_or_404(Usuario, id=usuario_id)

        if bolao.usuarios.filter(id=usuario.id).exists():
            return Response(
                {'detalhe': 'Este usuário já faz parte do bolão.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        bolao.usuarios.add(usuario)
        
        return Response(
            {'detalhe': f'Usuário {usuario.first_name} adicionado com sucesso ao bolão!'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='remover')
    def remover_usuario(self, request, pk=None):
        bolao = self.get_object()
        
        if bolao.dono != request.user:
            return Response(
                {'detalhe': 'Apenas o dono pode remover participantes neste bolão.'},
                status=status.HTTP_403_FORBIDDEN
            )

        usuario_id = request.data.get('usuario_id')
        if not usuario_id:
            return Response(
                {'detalhe': 'O campo "usuario_id" é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = get_object_or_404(Usuario, id=usuario_id)

        if not bolao.usuarios.filter(id=usuario.id).exists():
            return Response(
                {'detalhe': 'Este usuário não faz parte do bolão.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        bolao.usuarios.remove(usuario)
        
        return Response(
            {'detalhe': f'Usuário {usuario.first_name} removido com sucesso do bolão!'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='sair')
    def sair_bolao(self, request, pk=None):
        bolao = self.get_object()

        if not bolao.usuarios.filter(id=request.user.id).exists():
            return Response(
                {'detalhe': 'Você não está participando deste bolão.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        bolao.usuarios.remove(request.user)
        
        return Response(
            {'detalhe': 'Você saiu do bolão com sucesso.'},
            status=status.HTTP_200_OK
        )

class PalpiteModelViewSet(viewsets.ModelViewSet):
    filterset_fields = ['bolao']

    def get_queryset(self):
        usuario = self.request.user
        return Palpite.objects.filter(Q(dono=usuario)|Q(bolao__usuarios=usuario)|Q(bolao__dono=usuario)).distinct()
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PalpiteReadModelSerializer
        
        return PalpiteWriteModelSerializer
    
    def perform_create(self, serializer):
        serializer.save(dono=self.request.user)

    def perform_update(self, serializer):
        if self.get_object().dono != self.request.user:
            raise PermissionDenied('Apenas o dono pode editar este palpite.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.dono != self.request.user:
            raise PermissionDenied('Apenas o dono pode deletar este palpite.')
        instance.delete()