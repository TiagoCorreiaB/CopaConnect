from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.hashers import make_password
from .models import Usuario, Perfil, Amizade

class UsuarioWriteModelSerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source='username')
    senha = serializers.CharField(source='password', write_only=True)

    class Meta:
        model = Usuario
        fields = ['id','usuario','senha','email', 'telefone']

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
    usuario = serializers.ReadOnlyField(source='username')
    foto = serializers.SerializerMethodField()
    apelido = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id','usuario','foto','apelido','online']

    def get_foto(self, obj):
        try:
            if obj.perfil and obj.perfil.foto:
                return obj.perfil.foto.url
        except Exception:
            pass
        return None

    def get_apelido(self, obj):
        try:
            if obj.perfil and obj.perfil.apelido:
                return obj.perfil.apelido
        except Exception:
            pass
        return obj.username


class UsuarioRetrieveModelSerializer(serializers.ModelSerializer):
    usuario = serializers.ReadOnlyField(source='username')
    foto = serializers.SerializerMethodField()
    apelido = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'usuario', 'foto', 'apelido', 'email', 'telefone', 'online']

    def get_foto(self, obj):
        try:
            if obj.perfil and obj.perfil.foto:
                return obj.perfil.foto.url
        except Exception:
            pass
        return None

    def get_apelido(self, obj):
        try:
            if obj.perfil and obj.perfil.apelido:
                return obj.perfil.apelido
        except Exception:
            pass
        return obj.username

class PerfilWriteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id','usuario','foto','apelido','descricao']
        read_only_fields = ['usuario']

class PerfilReadModelSerializer(serializers.ModelSerializer):
    usuario = UsuarioReadModelSerializer(read_only=True)
    foto = serializers.SerializerMethodField()

    class Meta:
        model = Perfil
        fields = ['id','usuario','foto','apelido','descricao']

    def get_foto(self, obj):
        try:
            return obj.foto.url
        except Exception:
            return None

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