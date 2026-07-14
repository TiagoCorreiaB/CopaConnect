from django.contrib import admin
from .models import Usuario, Perfil, Amizade

@admin.register(Usuario)
class UsuarioModelAdmin(admin.ModelAdmin):
    list_display = ('id','exibir_usuario','exibir_nome','exibir_sobrenome','email','telefone','exibir_ultimo_login')

    @admin.display(description='usuario')
    def exibir_usuario(self, obj):
        return obj.username
    
    @admin.display(description='nome')
    def exibir_nome(self, obj):
        return obj.first_name
    
    @admin.display(description='sobrenome')
    def exibir_sobrenome(self, obj):
        return obj.last_name
    
    @admin.display(description='ultimo login')
    def exibir_ultimo_login(self, obj):
        return obj.last_login

@admin.register(Perfil)
class PerfilModelAdmin(admin.ModelAdmin):
    list_display = ('id','usuario','foto','apelido','descricao')

@admin.register(Amizade)
class AmizadeModelAdmin(admin.ModelAdmin):
    list_display = ('id','usuario','amigo','status')