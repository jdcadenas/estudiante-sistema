from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum
from django.template.loader import get_template
from .models import PerfilEstudiante, Asistencia, SolicitudPermiso, Feedback, Usuario, Curso
from .forms import RegistroUsuarioForm, PerfilEstudianteForm, SolicitudPermisoForm, FeedbackForm, EdicionUsuarioForm
from io import BytesIO
from datetime import date
from xhtml2pdf import pisa

# Vista de inicio
def home(request):
    """
    Muestra la página de inicio.
    Si el usuario es administrador (staff), lo redirige al dashboard de admin.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard_admin')
    
    return render(request, 'home.html')

# --- Vistas de Autenticación y Registro ---

def registro(request):
    """
    Maneja el registro de nuevos usuarios y la creación de su perfil de estudiante.
    """
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        perfil_form = PerfilEstudianteForm(request.POST)
        if form.is_valid() and perfil_form.is_valid():
            # Crear el objeto de usuario pero no guardarlo todavía
            nuevo_usuario = form.save(commit=False)
            # Establecer la contraseña
            nuevo_usuario.set_password(form.cleaned_data['password'])
            # Guardar el usuario
            nuevo_usuario.save()
            
            # Crear el perfil del estudiante
            perfil = perfil_form.save(commit=False)
            perfil.usuario = nuevo_usuario
            perfil.save()
            
            messages.success(request, '¡Tu cuenta ha sido creada exitosamente! Ya puedes iniciar sesión.')
            return redirect('home')
    else:
        form = RegistroUsuarioForm()
        perfil_form = PerfilEstudianteForm()
        
    return render(request, 'registration/registro.html', {
        'form': form,
        'perfil_form': perfil_form
    })

# --- Vistas del Módulo de Estudiante ---

@login_required
def solicitar_permiso(request):
    """
    Permite al estudiante enviar una solicitud de permiso.
    """
    if request.method == 'POST':
        form = SolicitudPermisoForm(request.POST)
        if form.is_valid():
            permiso = form.save(commit=False)
            permiso.estudiante = request.user.perfil_estudiante
            permiso.save()
            messages.success(request, 'Tu solicitud de permiso ha sido enviada.')
            return redirect('historial_permisos')
    else:
        form = SolicitudPermisoForm()
    
    return render(request, 'estudiante/solicitar_permiso.html', {'form': form})

@login_required
def historial_permisos(request):
    """
    Muestra el historial de permisos solicitados por el estudiante.
    """
    solicitudes = SolicitudPermiso.objects.filter(estudiante=request.user.perfil_estudiante).order_by('-fecha_creacion')
    return render(request, 'estudiante/historial_permisos.html', {'solicitudes': solicitudes})

@login_required
def enviar_feedback(request):
    """
    Permite al estudiante enviar feedback.
    """
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.estudiante = request.user.perfil_estudiante
            feedback.save()
            messages.success(request, 'Gracias por tu feedback. Ha sido enviado correctamente.')
            return redirect('home')
    else:
        form = FeedbackForm()
        
    return render(request, 'estudiante/enviar_feedback.html', {'form': form})

# --- Vistas del Módulo de Administración ---

def es_admin(user):
    """
    Verifica si un usuario es administrador (staff o superuser).
    """
    return user.is_staff or user.is_superuser



# ... (otras vistas)

@login_required
@user_passes_test(es_admin)
def dashboard_admin(request):
    """
    Dashboard principal para el administrador con información más detallada y filtrada por cursos asignados.
    Permite filtrar por un curso específico.
    """
    # Obtener cursos que el administrador puede gestionar
    if request.user.is_superuser:
        cursos_gestionables = Curso.objects.all()
    else:
        cursos_gestionables = request.user.cursos_asignados.all()

    # Obtener el ID del curso seleccionado del request GET
    curso_id = request.GET.get('curso', None)
    curso_seleccionado = None

    estudiantes_queryset = PerfilEstudiante.objects.all()
    solicitudes_queryset = SolicitudPermiso.objects.all()

    if curso_id:
        try:
            curso_seleccionado = Curso.objects.get(pk=curso_id)
            # Verificar si el admin tiene permiso para ver este curso
            if not request.user.is_superuser and curso_seleccionado not in cursos_gestionables:
                return HttpResponseForbidden("No tienes permiso para ver este curso.")
            
            # Filtrar querysets por el curso seleccionado
            estudiantes_queryset = estudiantes_queryset.filter(curso=curso_seleccionado)
            solicitudes_queryset = solicitudes_queryset.filter(estudiante__curso=curso_seleccionado)
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no es válido.")
            # Continuar sin filtro de curso
            curso_id = None # Reiniciar para no intentar filtrar con un ID inválido
    
    # Si no hay curso_id y el admin no es superuser, filtrar por sus cursos asignados (todos combinados)
    if not request.user.is_superuser and not curso_id:
        estudiantes_queryset = estudiantes_queryset.filter(curso__in=cursos_gestionables)
        solicitudes_queryset = solicitudes_queryset.filter(estudiante__curso__in=cursos_gestionables)

    # Resumen numérico
    total_estudiantes = estudiantes_queryset.count()
    permisos_pendientes_count = solicitudes_queryset.filter(estado='PENDIENTE').count()
    
    # Listas de actividad reciente
    ultimos_estudiantes = estudiantes_queryset.order_by('-usuario__date_joined')[:5]
    ultimos_permisos_pendientes = solicitudes_queryset.filter(estado='PENDIENTE').order_by('-fecha_creacion')[:5]
    
    context = {
        'cursos_disponibles': cursos_gestionables,
        'curso_seleccionado': curso_seleccionado,
        'total_estudiantes': total_estudiantes,
        'permisos_pendientes': permisos_pendientes_count,
        'ultimos_estudiantes': ultimos_estudiantes,
        'ultimos_permisos_pendientes': ultimos_permisos_pendientes,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(es_admin)
def lista_estudiantes(request):
    """
    Muestra una lista de todos los estudiantes para CRUD, filtrada por cursos asignados al admin.
    Permite filtrar por un curso específico.
    """
    # Obtener cursos que el administrador puede gestionar
    if request.user.is_superuser:
        cursos_gestionables = Curso.objects.all()
        estudiantes_queryset = PerfilEstudiante.objects.all()
    else:
        cursos_gestionables = request.user.cursos_asignados.all()
        estudiantes_queryset = PerfilEstudiante.objects.filter(curso__in=cursos_gestionables)

    # Obtener el ID del curso seleccionado del request GET
    curso_id = request.GET.get('curso', None)
    curso_seleccionado = None

    if curso_id:
        try:
            curso_seleccionado = Curso.objects.get(pk=curso_id)
            # Verificar si el admin tiene permiso para ver este curso
            if not request.user.is_superuser and curso_seleccionado not in cursos_gestionables:
                return HttpResponseForbidden("No tienes permiso para ver estudiantes de este curso.")
            
            # Filtrar queryset por el curso seleccionado
            estudiantes_queryset = estudiantes_queryset.filter(curso=curso_seleccionado)
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no es válido.")
            curso_id = None
    
    estudiantes = estudiantes_queryset.order_by('apellidos', 'nombres')

    context = {
        'cursos_disponibles': cursos_gestionables,
        'curso_seleccionado': curso_seleccionado,
        'estudiantes': estudiantes,
    }
    return render(request, 'admin/estudiantes_lista.html', context)

@login_required
@user_passes_test(es_admin)
def crear_estudiante(request):
    """
    Crea un nuevo estudiante y su usuario asociado.
    """
    if request.method == 'POST':
        user_form = RegistroUsuarioForm(request.POST)
        profile_form = PerfilEstudianteForm(request.POST, user=request.user)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            profile = profile_form.save(commit=False)
            profile.usuario = user
            profile.save()
            messages.success(request, f'Estudiante "{user.username}" creado exitosamente.')
            return redirect('lista_estudiantes')
    else:
        user_form = RegistroUsuarioForm()
        profile_form = PerfilEstudianteForm(user=request.user)
    
    return render(request, 'admin/estudiante_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'titulo': 'Añadir Nuevo Estudiante'
    })

@login_required
@user_passes_test(es_admin)
def editar_estudiante(request, pk):
    """
    Edita los datos de un estudiante.
    """
    perfil = get_object_or_404(PerfilEstudiante, pk=pk)
    usuario = perfil.usuario
    
    if request.method == 'POST':
        user_form = EdicionUsuarioForm(request.POST, instance=usuario)
        profile_form = PerfilEstudianteForm(request.POST, instance=perfil, user=request.user)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'Datos del estudiante "{usuario.username}" actualizados correctamente.')
            return redirect('lista_estudiantes')
    else:
        user_form = EdicionUsuarioForm(instance=usuario)
        profile_form = PerfilEstudianteForm(instance=perfil, user=request.user)
        
    return render(request, 'admin/estudiante_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'titulo': 'Editar Estudiante'
    })

@login_required
@user_passes_test(es_admin)
def eliminar_estudiante(request, pk):
    """
    Elimina a un estudiante, verificando permisos por curso.
    """
    perfil = get_object_or_404(PerfilEstudiante, pk=pk)

    # Restricción por curso para administradores no superusuario
    if not request.user.is_superuser:
        if perfil.curso not in request.user.cursos_asignados.all():
            return HttpResponseForbidden("No tienes permiso para eliminar estudiantes de este curso.")

    if request.method == 'POST':
        # El usuario se elimina en cascada gracias a la configuración del modelo
        perfil.usuario.delete()
        messages.success(request, f'Estudiante "{perfil.nombres} {perfil.apellidos}" eliminado correctamente.')
        return redirect('lista_estudiantes')
    
    return render(request, 'admin/estudiante_confirm_delete.html', {'estudiante': perfil})

@login_required
@user_passes_test(es_admin)
def tomar_asistencia(request):
    """
    Muestra la interfaz para tomar la asistencia del día, filtrada por cursos asignados al admin.
    Permite filtrar por un curso específico.
    """
    hoy = timezone.localdate()
    
    if request.user.is_superuser:
        cursos_gestionables = Curso.objects.all()
        estudiantes_base_queryset = PerfilEstudiante.objects.all()
    else:
        cursos_gestionables = request.user.cursos_asignados.all()
        estudiantes_base_queryset = PerfilEstudiante.objects.filter(curso__in=cursos_gestionables)

    curso_id = request.GET.get('curso', None)
    curso_seleccionado = None

    estudiantes_queryset = estudiantes_base_queryset

    if curso_id:
        try:
            curso_seleccionado = Curso.objects.get(pk=curso_id)
            if not request.user.is_superuser and curso_seleccionado not in cursos_gestionables:
                return HttpResponseForbidden("No tienes permiso para tomar asistencia para este curso.")
            
            estudiantes_queryset = estudiantes_queryset.filter(curso=curso_seleccionado)
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no es válido.")
            curso_id = None
    
    estudiantes = estudiantes_queryset.order_by('apellidos', 'nombres')
    
    # WORKAROUND: Usar un rango de fechas para evitar el error 'user-defined function raised exception' de SQLite.
    start_of_day = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.min.time()))
    end_of_day = start_of_day + timezone.timedelta(days=1)
    
    asistencias_hoy = Asistencia.objects.filter(
        fecha__gte=start_of_day,
        fecha__lt=end_of_day,
        estudiante__in=estudiantes_queryset
    ).select_related('estudiante')
    
    asistencias_por_estudiante = {asistencia.estudiante.pk: asistencia.esta_presente for asistencia in asistencias_hoy}

    # Obtener las horas guardadas para mostrarlas en el selector
    horas_academicas_guardadas = 2  # Valor por defecto
    if asistencias_hoy.exists():
        horas_academicas_guardadas = asistencias_hoy.first().horas_academicas

    for est in estudiantes:
        est.asistio_hoy = asistencias_por_estudiante.get(est.pk, False)

    context = {
        'cursos_disponibles': cursos_gestionables,
        'curso_seleccionado': curso_seleccionado,
        'estudiantes': estudiantes,
        'hoy': hoy,
        'asistencia_tomada': asistencias_hoy.exists(),
        'horas_academicas_guardadas': horas_academicas_guardadas,
    }
    return render(request, 'admin/tomar_asistencia.html', context)

@login_required
@user_passes_test(es_admin)
def guardar_asistencia(request):
    """
    Guarda los datos de asistencia enviados desde el formulario, filtrando por cursos del admin.
    Lógica simplificada: para todos los estudiantes relevantes, si está marcado -> presente, si no -> ausente.
    """
    if request.method == 'POST':
        hoy_date = timezone.localdate()
        ids_presentes = set(request.POST.getlist('presentes'))
        horas_academicas_str = request.POST.get('horas_academicas', '2') # Default to '2'
        try:
            horas_academicas = int(horas_academicas_str)
        except (ValueError, TypeError):
            horas_academicas = 2 # Fallback to default if conversion fails

        curso_id = request.GET.get('curso', None)
        
        if request.user.is_superuser:
            cursos_gestionables = Curso.objects.all()
            estudiantes_a_gestionar_queryset = PerfilEstudiante.objects.all()
        else:
            cursos_gestionables = request.user.cursos_asignados.all()
            estudiantes_a_gestionar_queryset = PerfilEstudiante.objects.filter(curso__in=cursos_gestionables)

        if curso_id:
            try:
                curso_seleccionado = Curso.objects.get(pk=curso_id)
                if not request.user.is_superuser and curso_seleccionado not in cursos_gestionables:
                    messages.error(request, "No tienes permiso para gestionar este curso.")
                    return redirect(reverse('tomar_asistencia'))
                
                estudiantes_a_gestionar_queryset = estudiantes_a_gestionar_queryset.filter(curso=curso_seleccionado)
            except Curso.DoesNotExist:
                messages.error(request, "El curso seleccionado no es válido.")
                return redirect(reverse('tomar_asistencia'))
            
        for estudiante in estudiantes_a_gestionar_queryset:
            esta_presente = str(estudiante.pk) in ids_presentes
            
            start_of_day = timezone.make_aware(timezone.datetime.combine(hoy_date, timezone.datetime.min.time()))
            end_of_day = start_of_day + timezone.timedelta(days=1)

            asistencia_hoy = Asistencia.objects.filter(
                estudiante=estudiante,
                fecha__gte=start_of_day,
                fecha__lt=end_of_day
            ).first()

            if asistencia_hoy:
                asistencia_hoy.esta_presente = esta_presente
                asistencia_hoy.fecha = timezone.now()
                asistencia_hoy.horas_academicas = horas_academicas
                asistencia_hoy.save(update_fields=['esta_presente', 'fecha', 'horas_academicas'])
            else:
                Asistencia.objects.create(
                    estudiante=estudiante,
                    esta_presente=esta_presente,
                    horas_academicas=horas_academicas,
                )
        
        messages.success(request, 'La asistencia ha sido guardada/actualizada correctamente.')
        
        redirect_url = reverse('tomar_asistencia')
        if curso_id:
            redirect_url += f"?curso={curso_id}"
        return redirect(redirect_url)

    redirect_url = reverse('tomar_asistencia')
    if request.GET.get('curso', None):
        redirect_url += f"?curso={request.GET.get('curso')}"
    return redirect(redirect_url)

@login_required
@user_passes_test(es_admin)
def vista_reportes_cursos(request):
    """
    Muestra una lista de cursos para generar reportes.
    """
    if request.user.is_superuser:
        cursos_gestionables = Curso.objects.all()
    else:
        cursos_gestionables = request.user.cursos_asignados.all()
    
    context = {
        'cursos': cursos_gestionables.order_by('nombre')
    }
    return render(request, 'admin/reportes_cursos.html', context)


@login_required
@user_passes_test(es_admin)
def generar_reporte_asistencia_pdf(request, curso_id):
    """
    Genera un reporte de asistencia en formato PDF para un curso dado.
    """
    curso = get_object_or_404(Curso, pk=curso_id)

    # Verificar permisos del administrador para este curso
    if not request.user.is_superuser and curso not in request.user.cursos_asignados.all():
        messages.error(request, "No tiene permiso para generar reportes de este curso.")
        return redirect('vista_reportes_cursos') # O a donde sea apropiado

    # Datos del facilitador (administrador logueado)
    facilitador_nombre = request.user.get_full_name() or request.user.username
    
    # Obtener estudiantes del curso
    estudiantes_del_curso = PerfilEstudiante.objects.filter(curso=curso).order_by('apellidos', 'nombres')

    datos_estudiantes_reporte = []
    for estudiante in estudiantes_del_curso:
        asistencias_estudiante = Asistencia.objects.filter(
            estudiante=estudiante,
            # Considerar solo asistencias marcadas como presentes
            esta_presente=True
        ).order_by('fecha')

        # Calcular total de horas académicas asistidas
        total_horas_asistidas = asistencias_estudiante.aggregate(Sum('horas_academicas'))['horas_academicas__sum'] or 0

        # Recopilar fechas y horas de asistencia, incluyendo las horas académicas de cada registro
        fechas_y_horas_asistencia = [
            f'{asist.fecha.strftime("%d/%m/%Y %H:%M")} ({asist.horas_academicas} {"hora" if asist.horas_academicas == 1 else "horas"})'
            for asist in asistencias_estudiante
        ]

        datos_estudiantes_reporte.append({
            'nombre_completo': f"{estudiante.nombres} {estudiante.apellidos}",
            'cedula': estudiante.cedula,
            'telefono': estudiante.telefono, # Asumiendo que el campo 'telefono' está directamente en PerfilEstudiante
            'email': estudiante.usuario.email,
            'total_horas_asistidas': total_horas_asistidas,
            'fechas_y_horas_asistencia': fechas_y_horas_asistencia,
        })

    context = {
        'curso_nombre': curso.nombre,
        'facilitador_nombre': facilitador_nombre,
        'fecha_emision': date.today().strftime("%d/%m/%Y"),
        'estudiantes': datos_estudiantes_reporte,
        'logo_path': request.build_absolute_uri('/static/img/iujo_logo.png') # Asegúrate de que el logo exista aquí
    }

    template_path = 'admin/reporte_asistencia_template.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_asistencia_{curso.codigo}_{date.today().strftime("%Y%m%d")}.pdf"'

    pisa_status = pisa.CreatePDF(
        html,                # the HTML to convert
        dest=response,       # file handle to receive result
        encoding="UTF-8"
    )
    if pisa_status.err:
        messages.error(request, "Hubo un error al generar el PDF.")
        return redirect('vista_reportes_cursos')
    return response

@login_required
@user_passes_test(es_admin)
def reporte_inasistencias(request):
    """
    Muestra un reporte de asistencia filtrado por fecha y cursos asignados al admin.
    Permite filtrar por un curso específico y muestra el estado de todos los estudiantes.
    """
    fecha_filtro_str = request.GET.get('fecha', None)
    
    if fecha_filtro_str:
        fecha_filtro = timezone.datetime.strptime(fecha_filtro_str, '%Y-%m-%d').date()
    else:
        fecha_filtro = timezone.localdate()
    
    if request.user.is_superuser:
        cursos_gestionables = Curso.objects.all()
        estudiantes_gestionables_base = PerfilEstudiante.objects.all()
    else:
        cursos_gestionables = request.user.cursos_asignados.all()
        estudiantes_gestionables_base = PerfilEstudiante.objects.filter(curso__in=cursos_gestionables)

    curso_id = request.GET.get('curso', None)
    curso_seleccionado = None

    estudiantes_gestionables_queryset = estudiantes_gestionables_base

    if curso_id:
        try:
            curso_seleccionado = Curso.objects.get(pk=curso_id)
            if not request.user.is_superuser and curso_seleccionado not in cursos_gestionables:
                return HttpResponseForbidden("No tienes permiso para ver reportes de este curso.")
            
            estudiantes_gestionables_queryset = estudiantes_gestionables_queryset.filter(curso=curso_seleccionado)
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no es válido.")
            curso_id = None
    
    estudiantes = estudiantes_gestionables_queryset.order_by('apellidos', 'nombres')

    # WORKAROUND: Usar un rango de fechas para evitar el error 'user-defined function raised exception' de SQLite.
    start_of_day = timezone.make_aware(timezone.datetime.combine(fecha_filtro, timezone.datetime.min.time()))
    end_of_day = start_of_day + timezone.timedelta(days=1)

    asistencias_del_dia = Asistencia.objects.filter(
        fecha__gte=start_of_day,
        fecha__lt=end_of_day,
        estudiante__in=estudiantes_gestionables_queryset
    ).values('estudiante__pk', 'esta_presente')

    asistencias_map = {item['estudiante__pk']: item['esta_presente'] for item in asistencias_del_dia}

    for estudiante in estudiantes:
        estudiante.estado_asistencia = asistencias_map.get(estudiante.pk)

    context = {
        'cursos_disponibles': cursos_gestionables,
        'curso_seleccionado': curso_seleccionado,
        'estudiantes': estudiantes,
        'fecha_filtro': fecha_filtro
    }
    return render(request, 'admin/reporte_inasistencias.html', context)

@login_required
@user_passes_test(es_admin)
def gestionar_permisos(request):
    """
    Muestra las solicitudes de permiso para aprobarlas o rechazarlas, filtradas por cursos del admin.
    Permite filtrar por un curso específico.
    """
    # Obtener cursos que el administrador puede gestionar
    if request.user.is_superuser:
        cursos_gestionables = Curso.objects.all()
        solicitudes_queryset = SolicitudPermiso.objects.all()
    else:
        cursos_gestionables = request.user.cursos_asignados.all()
        solicitudes_queryset = SolicitudPermiso.objects.filter(estudiante__curso__in=cursos_gestionables)

    # Obtener el ID del curso seleccionado del request GET
    curso_id = request.GET.get('curso', None)
    curso_seleccionado = None

    if curso_id:
        try:
            curso_seleccionado = Curso.objects.get(pk=curso_id)
            # Verificar si el admin tiene permiso para ver este curso
            if not request.user.is_superuser and curso_seleccionado not in cursos_gestionables:
                return HttpResponseForbidden("No tienes permiso para gestionar permisos de este curso.")
            
            # Filtrar queryset por el curso seleccionado
            solicitudes_queryset = solicitudes_queryset.filter(estudiante__curso=curso_seleccionado)
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no es válido.")
            curso_id = None
    
    solicitudes = solicitudes_queryset.order_by('-fecha_creacion')

    context = {
        'cursos_disponibles': cursos_gestionables,
        'curso_seleccionado': curso_seleccionado,
        'solicitudes': solicitudes,
    }
    return render(request, 'admin/gestionar_permisos.html', context)

@login_required
@user_passes_test(es_admin)
def aprobar_permiso(request, pk):
    """
    Aprueba una solicitud de permiso, verificando permisos por curso.
    """
    solicitud = get_object_or_404(SolicitudPermiso, pk=pk)

    # Restricción por curso para administradores no superusuario
    if not request.user.is_superuser:
        if solicitud.estudiante.curso not in request.user.cursos_asignados.all():
            return HttpResponseForbidden("No tienes permiso para aprobar solicitudes de permiso de estudiantes de este curso.")

    if request.method == 'POST':
        solicitud.estado = SolicitudPermiso.Estado.APROBADO
        solicitud.save()
        messages.success(request, f'La solicitud de {solicitud.estudiante} ha sido aprobada.')
    return redirect('gestionar_permisos')

@login_required
@user_passes_test(es_admin)
def rechazar_permiso(request, pk):
    """
    Rechaza una solicitud de permiso, verificando permisos por curso.
    """
    solicitud = get_object_or_404(SolicitudPermiso, pk=pk)

    # Restricción por curso para administradores no superusuario
    if not request.user.is_superuser:
        if solicitud.estudiante.curso not in request.user.cursos_asignados.all():
            return HttpResponseForbidden("No tienes permiso para rechazar solicitudes de permiso de estudiantes de este curso.")

    if request.method == 'POST':
        solicitud.estado = SolicitudPermiso.Estado.RECHAZADO
        solicitud.save()
        messages.warning(request, f'La solicitud de {solicitud.estudiante} ha sido rechazada.')
    return redirect('gestionar_permisos')

@login_required
@user_passes_test(es_admin)
def lista_feedback(request):
    """
    Muestra una lista de todos los feedbacks enviados por los estudiantes, filtrada por cursos del admin.
    Permite filtrar por un curso específico.
    """
    # Obtener cursos que el administrador puede gestionar
    if request.user.is_superuser:
        cursos_gestionables = Curso.objects.all()
        feedbacks_queryset = Feedback.objects.all()
    else:
        cursos_gestionables = request.user.cursos_asignados.all()
        feedbacks_queryset = Feedback.objects.filter(estudiante__curso__in=cursos_gestionables)

    # Obtener el ID del curso seleccionado del request GET
    curso_id = request.GET.get('curso', None)
    curso_seleccionado = None

    if curso_id:
        try:
            curso_seleccionado = Curso.objects.get(pk=curso_id)
            # Verificar si el admin tiene permiso para ver este curso
            if not request.user.is_superuser and curso_seleccionado not in cursos_gestionables:
                return HttpResponseForbidden("No tienes permiso para ver feedback de este curso.")
            
            # Filtrar queryset por el curso seleccionado
            feedbacks_queryset = feedbacks_queryset.filter(estudiante__curso=curso_seleccionado)
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no es válido.")
            curso_id = None
    
    feedbacks = feedbacks_queryset.order_by('-fecha_creacion')

    context = {
        'cursos_disponibles': cursos_gestionables,
        'curso_seleccionado': curso_seleccionado,
        'feedbacks': feedbacks,
    }
    return render(request, 'admin/lista_feedback.html', context)