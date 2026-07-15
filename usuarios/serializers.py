from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.hashers import make_password
from .models import Usuario, Perfil, Amizade

class UsuarioWriteModelSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='first_name', required=True)
    sobrenome = serializers.CharField(source='last_name', required=True)
    usuario = serializers.CharField(source='username')
    senha = serializers.CharField(source='password', write_only=True)

    class Meta:
        model = Usuario
        fields = ['id','usuario','nome','sobrenome','senha','email', 'telefone']

    def validate_senha(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return make_password(value)

    def validate_email(self, value):
        if self.instance and self.instance.email == value:
            return value

        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Este e-mail já está em uso.'
            )
        
        return value
    
    def validate_telefone(self, value):
        if len(value) < 11:
            raise serializers.ValidationError(
                'O número de telefone é inválido.'
            )

        if self.instance and self.instance.telefone == value:
            return value

        if Usuario.objects.filter(telefone=value).exists():
            raise serializers.ValidationError(
                'Este número já está em uso.'
            )
        
        return value

class UsuarioReadModelSerializer(serializers.ModelSerializer):
    nome = serializers.ReadOnlyField(source='first_name')
    sobrenome = serializers.ReadOnlyField(source='last_name')
    usuario = serializers.ReadOnlyField(source='username')

    class Meta:
        model = Usuario
        fields = ['id','usuario','nome','sobrenome']

class PerfilWriteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id','usuario','foto','apelido','descricao']
        read_only_fields = ['usuario']

class PerfilReadModelSerializer(serializers.ModelSerializer):
    usuario = UsuarioReadModelSerializer(read_only=True)

    class Meta:
        model = Perfil
        fields = ['id','usuario','foto','apelido','descricao']

class AmizadeWriteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Amizade
        fields = ['id','usuario','amigo','status']
        read_only_fields = ['usuario']

    def validate(self, attrs):
        request = self.context['request']
        
        if self.instance is None:
            amigo = attrs.get('amigo')
            
            if amigo == request.user:
                raise serializers.ValidationError(
                    'Você não pode ser seu próprio amigo.'
                )
                
            if Amizade.objects.filter(usuario=amigo, amigo=request.user).exists():
                raise serializers.ValidationError(
                    'Já existe um convite ou amizade entre vocês.'
                )
                
            attrs['status'] = Amizade.Status.PENDENTE

        else:
            novo_status = attrs.get('status')
            
            if self.instance.usuario == request.user and novo_status == Amizade.Status.ACEITO:
                raise serializers.ValidationError(
                    'Apenas o destinatário pode aceitar o convite.'
                )

        return attrs

class AmizadeReadModelSerializer(serializers.ModelSerializer):
    usuario = UsuarioReadModelSerializer(read_only=True)
    amigo = UsuarioReadModelSerializer(read_only=True)

    class Meta:
        model = Amizade
        fields = ['id','usuario','amigo','status']