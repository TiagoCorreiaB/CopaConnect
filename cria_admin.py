import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

def cria_superuser():
    User = get_user_model()
    
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    telefone = os.environ.get('DJANGO_SUPERUSER_TELEFONE')

    if not User.objects.filter(email=email).exists():
        print(f"Criando superusuário: {email}...")
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            telefone=telefone,
        )
        print("Superusuário criado com sucesso!")
    else:
        print(f"Superusuário com o e-mail '{email}' já existe.")

if __name__ == '__main__':
    cria_superuser()
