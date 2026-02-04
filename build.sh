#!/usr/bin/env bash
# build.sh

set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario si no existe (opcional)
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
" || true

# Colectar archivos estáticos
python manage.py collectstatic --no-input