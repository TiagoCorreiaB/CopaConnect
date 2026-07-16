#!/bin/sh

echo "=== Executando Migrations ==="
python manage.py migrate --noinput

echo "=== Coletando arquivos estaticos ==="
python manage.py collectstatic --noinput

echo "=== Verificando superusuario ==="
python cria_admin.py

echo "=== Iniciando Celery Worker ==="
celery -A core worker -l info --concurrency=1 &

echo "=== Iniciando Celery Beat ==="
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

echo "=== Iniciando Daphne Server ==="
exec daphne -b 0.0.0.0 -p 8000 core.asgi:application