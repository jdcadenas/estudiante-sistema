# Sistema de Asistencia Escolar

Este es un proyecto Django para gestionar la asistencia de estudiantes, solicitudes de permisos y feedback, con módulos separados para administradores y estudiantes.

## Tecnologías

- Python 3.x
- Django 5.x
- Bootstrap 5
- jQuery
- SQLite 3

## Configuración del Entorno

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL-DEL-REPOSITORIO>
    cd estudiante-sistema
    ```

2.  **Crear y activar un entorno virtual:**
    - En Windows:
      ```bash
      python -m venv env
      .\env\Scripts\activate
      ```
    - En macOS/Linux:
      ```bash
      python3 -m venv env
      source env/bin/activate
      ```

3.  **Instalar las dependencias:**
    Por ahora, la única dependencia principal es Django.
    ```bash
    pip install Django~=5.0
    ```
    *(Si en el futuro se añade un archivo `requirements.txt`, usar `pip install -r requirements.txt`)*

## Ejecución del Proyecto

1.  **Aplicar las migraciones:**
    Una vez configurado el entorno y con las dependencias instaladas, aplica las migraciones para crear la base de datos y sus tablas.
    ```bash
    python manage.py migrate
    ```

2.  **Crear un superusuario:**
    Para poder acceder al panel de administración de Django (`/admin`) y al módulo de administrador de la aplicación, necesitas una cuenta de superusuario.
    ```bash
    python manage.py createsuperuser
    ```
    Sigue las instrucciones en la consola para elegir un nombre de usuario, correo electrónico y contraseña.

3.  **Iniciar el servidor de desarrollo:**
    ```bash
    python manage.py runserver
    ```
    El sistema será accesible en `http://127.0.0.1:8000/`.

## Roles de Usuario

- **Administrador (Staff):**
  - Creado con el comando `createsuperuser`.
  - Tiene acceso al panel de Django en `/admin`.
  - Tiene acceso a las vistas de "Módulo Admin" en la aplicación web (Dashboard, Gestión de Estudiantes, Toma de Asistencia, etc.).
  - Para que una cuenta de usuario normal tenga permisos de administrador, edítala en el panel `/admin` y marca la casilla "Status de staff".

- **Estudiante:**
  - Puede registrarse a través del formulario público de la aplicación.
  - Tiene acceso a las vistas del "Módulo Estudiante" (Solicitar Permisos, ver historial, enviar feedback).
