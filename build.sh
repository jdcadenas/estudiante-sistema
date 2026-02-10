#!/usr/bin/env bash
set -o errexit

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario usando variables de entorno (más seguro)
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser \
        --no-input \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL || true
fi

# Colectar archivos estáticos
python manage.py collectstatic --no-input