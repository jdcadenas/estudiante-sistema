from django import forms
from .models import Usuario, PerfilEstudiante, SolicitudPermiso, Feedback, Curso

# FORMULARIO DE REGISTRO DE USUARIO
class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña')

    class Meta:
        model = Usuario
        fields = ['username']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cd['password2']

# FORMULARIO DE EDICION DE USUARIO
class EdicionUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username']

# FORMULARIO DE PERFIL DE ESTUDIANTE
class PerfilEstudianteForm(forms.ModelForm):
    class Meta:
        model = PerfilEstudiante
        fields = ['cedula', 'nombres', 'apellidos', 'grado', 'grupo', 'curso']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Extraer el usuario si se pasó
        super(PerfilEstudianteForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Filtrar los cursos disponibles si el usuario es un admin y no superuser
        if user and user.is_staff and not user.is_superuser:
            self.fields['curso'].queryset = user.cursos_asignados.all()

# FORMULARIO PARA SOLICITAR PERMISO
class SolicitudPermisoForm(forms.ModelForm):
    class Meta:
        model = SolicitudPermiso
        fields = ['fecha_inicio', 'fecha_fin', 'motivo']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

# FORMULARIO PARA ENVIAR FEEDBACK
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Escribe tu mensaje aquí...'}),
        }