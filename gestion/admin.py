from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, PerfilEstudiante, Curso, Asistencia, SolicitudPermiso, Feedback

# Personalizar la administración del modelo de Usuario
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('cursos_asignados',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('cursos_asignados',)}),
    )

admin.site.register(Usuario, CustomUserAdmin)

# Registrar el modelo Curso
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'descripcion')
    search_fields = ('nombre', 'codigo')

# Personalizar la administración del modelo PerfilEstudiante
@admin.register(PerfilEstudiante)
class PerfilEstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'cedula', 'grado', 'grupo', 'curso', 'usuario')
    list_filter = ('grado', 'grupo', 'curso')
    search_fields = ('nombres', 'apellidos', 'cedula', 'usuario__username')
    raw_id_fields = ('usuario',) # Para buscar usuarios más fácilmente en el admin

# Registrar los otros modelos
admin.site.register(Asistencia)
admin.site.register(SolicitudPermiso)
admin.site.register(Feedback)