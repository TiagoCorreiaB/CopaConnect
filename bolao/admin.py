from django.contrib import admin
from .models import Bolao, Palpite

@admin.register(Bolao)
class BolaoModelAdmin(admin.ModelAdmin):
    list_display = ('id','nome','descricao','partida','vencedor','status','get_usuarios','dono')

    @admin.display(description='qtd. usuarios') 
    def get_usuarios(self, obj):
        return obj.usuarios.count()

@admin.register(Palpite)
class PalpiteModelAdmin(admin.ModelAdmin):
    list_display = ('id','placar_1','placar_2','valor','data','usuario','bolao','pontuacao','valor_pontuacao')