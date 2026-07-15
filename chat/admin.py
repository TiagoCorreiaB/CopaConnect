from django.contrib import admin
from .models import Sala, Comentario

@admin.register(Sala)
class SalaModelAdmin(admin.ModelAdmin):
    list_display = ('id','nome','status','get_usuarios','partida')

    @admin.display(description='qtd. usuarios') 
    def get_usuarios(self, obj):
        return obj.usuarios.count()
    
@admin.register(Comentario)
class ComentarioModelAdmin(admin.ModelAdmin):
    list_display = ('id','sala','texto','usuario','data_envio')