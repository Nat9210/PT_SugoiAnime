from django import forms
from django.contrib.auth.models import User
from .models import Contenido, Perfil, Episodio

class ContenidoForm(forms.ModelForm):
    class Meta:
        model = Contenido
        fields = ['titulo', 'tipo', 'descripcion', 'año', 'duracion', 'idioma', 'imagen_portada', 'video_url', 'categorias']
        widgets = {
            'categorias': forms.CheckboxSelectMultiple,
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'tipo', 'avatar']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.HiddenInput(),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class EpisodioForm(forms.ModelForm):
    class Meta:
        model = Episodio
        fields = ['temporada', 'numero_episodio', 'titulo', 'descripcion', 'duracion', 'video_url']
