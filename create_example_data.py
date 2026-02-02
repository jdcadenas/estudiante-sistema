from gestion.models import Curso, Usuario, PerfilEstudiante
from django.utils import timezone
import random

# Clear existing courses and students to prevent duplicates if script is run multiple times
Curso.objects.all().delete()
PerfilEstudiante.objects.all().delete()
Usuario.objects.filter(is_superuser=False).delete() # Keep superuser

print("Creando cursos de ejemplo...")
cursos_data = [
    {'nombre': 'Matemáticas 101', 'codigo': 'MAT101', 'descripcion': 'Introducción a las matemáticas'},
    {'nombre': 'Ciencias Sociales', 'codigo': 'CSO202', 'descripcion': 'Estudio de la sociedad'},
    {'nombre': 'Historia Universal', 'codigo': 'HIS303', 'descripcion': 'Desde la antigüedad hasta el presente'},
]

cursos = []
for data in cursos_data:
    curso, created = Curso.objects.get_or_create(**data)
    cursos.append(curso)
    if created:
        print(f"Curso creado: {curso.nombre}")
    else:
        print(f"Curso ya existe: {curso.nombre}")

print("\nCreando 10 estudiantes de ejemplo...")
nombres = ["Ana", "Carlos", "María", "Pedro", "Sofía", "Jorge", "Laura", "Diego", "Elena", "Pablo"]
apellidos = ["González", "Rodríguez", "Martínez", "Sánchez", "Pérez", "Gómez", "Fernández", "Díaz", "Ruiz", "Torres"]
grados = ["1ro", "2do", "3ro"]
grupos = ["A", "B", "C"]

estudiantes_creados = []
for i in range(10):
    nombre = random.choice(nombres)
    apellido = random.choice(apellidos)
    username = f"{nombre.lower()}{apellido.lower()}{i}"
    email = f"{username}@ejemplo.com"
    password = "password123" # Contraseña sencilla para ejemplos
    grado = random.choice(grados)
    grupo = random.choice(grupos)
    curso = random.choice(cursos)
    cedula = f"12345678{i:02d}"

    # Crear Usuario
    user, user_created = Usuario.objects.get_or_create(username=username, email=email)
    if user_created:
        user.set_password(password)
        user.save()
        print(f"Usuario '{username}' creado.")
    else:
        print(f"Usuario '{username}' ya existe.")

    # Crear PerfilEstudiante
    perfil, perfil_created = PerfilEstudiante.objects.get_or_create(
        usuario=user,
        defaults={
            'cedula': cedula,
            'nombres': nombre,
            'apellidos': apellido,
            'grado': grado,
            'grupo': grupo,
            'curso': curso,
        }
    )
    if perfil_created:
        print(f"Estudiante '{nombre} {apellido}' (Cédula: {cedula}, Curso: {curso.nombre}) creado.")
        estudiantes_creados.append(perfil)
    else:
        print(f"Perfil de estudiante para '{username}' ya existe.")

# Asignar cursos al superusuario 'admin' para que pueda ver todos los cursos de ejemplo
admin_user = Usuario.objects.get(username='admin')
admin_user.cursos_asignados.set(cursos)
admin_user.save()
print("\nCursos asignados al superusuario 'admin'.")

print("\nDatos de ejemplo creados exitosamente.")
