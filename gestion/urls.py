from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # URLs Generales
    path('', views.home, name='home'),
    path('registro/', views.registro, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # URLs para Estudiantes
    path('permiso/solicitar/', views.solicitar_permiso, name='solicitar_permiso'),
    path('permiso/historial/', views.historial_permisos, name='historial_permisos'),
    path('feedback/enviar/', views.enviar_feedback, name='enviar_feedback'),

    # URLs para Administradores
    path('admin/dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('admin/estudiantes/', views.lista_estudiantes, name='lista_estudiantes'),
    path('admin/estudiantes/nuevo/', views.crear_estudiante, name='crear_estudiante'),
    path('admin/estudiantes/editar/<int:pk>/', views.editar_estudiante, name='editar_estudiante'),
    path('admin/estudiantes/eliminar/<int:pk>/', views.eliminar_estudiante, name='eliminar_estudiante'),
    
    path('admin/asistencia/', views.tomar_asistencia, name='tomar_asistencia'),
    path('admin/asistencia/guardar/', views.guardar_asistencia, name='guardar_asistencia'),
    path('admin/reporte/inasistencias/', views.reporte_inasistencias, name='reporte_inasistencias'),
    path('admin/reportes/cursos/', views.vista_reportes_cursos, name='vista_reportes_cursos'),
    path('admin/reporte/asistencia/<int:curso_id>/pdf/', views.generar_reporte_asistencia_pdf, name='generar_reporte_asistencia_pdf'),

    path('admin/permisos/', views.gestionar_permisos, name='gestionar_permisos'),
    path('admin/permisos/aprobar/<int:pk>/', views.aprobar_permiso, name='aprobar_permiso'),
    path('admin/permisos/rechazar/<int:pk>/', views.rechazar_permiso, name='rechazar_permiso'),
    path('admin/feedback/', views.lista_feedback, name='lista_feedback'),
    
    path('sistema/keep-alive/', views.despertar_db, name='keep_alive'),
]
