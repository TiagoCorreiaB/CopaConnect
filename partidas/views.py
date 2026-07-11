from rest_framework import viewsets
from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Partida
from .serializers import PartidaModelSerializer

class PartidaFilter(filters.FilterSet):
    time = filters.CharFilter(method='filter_por_time')

    class Meta:
        model = Partida
        fields = ['status', 'fase', 'data'] 

    def filter_por_time(self, queryset, name, value):
        return queryset.filter(Q(time_1__icontains=value)|Q(time_2__icontains=value))

class PartidaReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Partida.objects.all()
    serializer_class = PartidaModelSerializer
    filterset_class = PartidaFilter