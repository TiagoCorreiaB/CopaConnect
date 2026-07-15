from django.contrib import admin
from .models import Partida

@admin.register(Partida)
class PartidaModelAdmin(admin.ModelAdmin):
    list_display = ('id','time_1','time_2','placar_1','placar_2','data','status','tempo','fase','estatisticas_finais')