from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

# MODELO DE USUARIO PERSONALIZADO
class Usuario(AbstractUser):
    """
    Se extiende el usuario por defecto de Django para futuras personalizaciones.
    """
    cursos_asignados = models.ManyToManyField(
        'Curso',
        related_name='administradores',
        blank=True,
        verbose_name='Cursos Asignados'
    )

# MODELO DE CURSO
class Curso(models.Model):
    """
    Representa un curso en el sistema.
    """
    nombre = models.CharField('Nombre del Curso', max_length=100)
    codigo = models.CharField('Código del Curso', max_length=20, unique=True)
    descripcion = models.TextField('Descripción', blank=True, null=True)

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['nombre']

# MODELO DE PERFIL DE ESTUDIANTE
class PerfilEstudiante(models.Model):
    """
    Almacena la información específica de cada estudiante, vinculado a una cuenta de usuario.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_estudiante',
        verbose_name='Usuario'
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estudiantes',
        verbose_name='Curso'
    )
    cedula = models.CharField('Cédula', max_length=20, unique=True, help_text='Cédula de identidad del estudiante.')
    nombres = models.CharField('Nombres', max_length=100)
    apellidos = models.CharField('Apellidos', max_length=100)
    grupo = models.CharField('Grupo', max_length=50, blank=True, null=True)
    grado = models.CharField('Grado', max_length=50, blank=True, null=True)
    telefono = models.CharField('Número de Teléfono', max_length=20)

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'

    class Meta:
        verbose_name = 'Perfil de Estudiante'
        verbose_name_plural = 'Perfiles de Estudiantes'
        ordering = ['apellidos', 'nombres']

# MODELO DE ASISTENCIA
class Asistencia(models.Model):
    """
    Registra la asistencia diaria de cada estudiante.
    """
    estudiante = models.ForeignKey(
        PerfilEstudiante,
        on_delete=models.CASCADE,
        related_name='asistencias',
        verbose_name='Estudiante'
    )
    fecha = models.DateTimeField('Fecha y Hora', default=timezone.now)
    horas_academicas = models.PositiveIntegerField('Horas Académicas', default=2)
    esta_presente = models.BooleanField('¿Está Presente?', default=False)

    def __str__(self):
        estado = "Presente" if self.esta_presente else "Ausente"
        return f'{self.estudiante} - {self.fecha.strftime("%Y-%m-%d %H:%M")} ({estado})'

    class Meta:
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        ordering = ['-fecha', 'estudiante']

# MODELO DE SOLICITUD DE PERMISO
class SolicitudPermiso(models.Model):
    """
    Permite a los estudiantes solicitar permisos por ausencia.
    """
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    estudiante = models.ForeignKey(
        PerfilEstudiante,
        on_delete=models.CASCADE,
        related_name='solicitudes_permiso',
        verbose_name='Estudiante'
    )
    fecha_inicio = models.DateField('Fecha de Inicio')
    fecha_fin = models.DateField('Fecha de Fin')
    motivo = models.TextField('Motivo de la solicitud')
    estado = models.CharField(
        'Estado',
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Permiso para {self.estudiante} - {self.get_estado_display()}'

    class Meta:
        verbose_name = 'Solicitud de Permiso'
        verbose_name_plural = 'Solicitudes de Permiso'
        ordering = ['-fecha_creacion']

# MODELO DE FEEDBACK
class Feedback(models.Model):
    """
    Permite a los estudiantes enviar comentarios al personal administrativo.
    """
    estudiante = models.ForeignKey(
        PerfilEstudiante,
        on_delete=models.SET_NULL,
        null=True,
        related_name='feedbacks',
        verbose_name='Estudiante'
    )
    mensaje = models.TextField('Mensaje')
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)

    def __str__(self):
        return f'Feedback de {self.estudiante} el {self.fecha_creacion.strftime("%d/%m/%Y")}'

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
        ordering = ['-fecha_creacion']