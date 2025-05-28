import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import ContenidoForm, UserUpdateForm, PerfilUpdateForm
from .models import Contenido, Categoria, Episodio, ContenidoCategoria, Perfil
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import re

# Vistas que solo renderizan plantillas estáticas, sin conexión a la base de datos

@login_required
def index(request):
    return render(request, 'myapp/index.html')

@login_required
def render_anime_details(request):
    return render(request, 'myapp/anime-details.html')

@login_required
def render_anime_watching(request):
    return render(request, 'myapp/anime-watching.html')

@login_required
def render_blog_details(request):
    return render(request, 'myapp/blog-details.html')

@login_required
def render_blog(request):
    return render(request, 'myapp/blog.html')

def render_login(request):
    return render(request, 'myapp/login.html')

def render_signup(request):
    return render(request, 'myapp/signup.html')

@login_required
def render_categories(request):
    return render(request, 'myapp/categories.html')

@login_required
def render_catalogo(request):
    return render(request, 'myapp/catalogo.html')

#vistas conectadas a la base de datos
@login_required
def perfil_view(request):
    user = request.user
    seccion = request.GET.get('seccion', 'datos')
    perfil = user.perfiles.first()
    if not perfil:
        # Si el usuario no tiene perfil, crear uno por defecto
        perfil = Perfil.objects.create(usuario=user, nombre=user.username, tipo='adulto')

    user_form = UserUpdateForm(instance=user)
    perfil_form = PerfilUpdateForm(instance=perfil)
    contenidos = None
    if seccion == 'gestion' and user.is_staff:
        contenidos = Contenido.objects.all()

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        perfil_form = PerfilUpdateForm(request.POST, request.FILES, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            return redirect('perfil')

    return render(request, 'myapp/perfil.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'perfil': perfil,
        'seccion': seccion,
        'contenidos': contenidos,
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'myapp/login.html', {'error': 'Usuario o contraseña incorrectas'})
    return render(request, 'myapp/login.html')

def validate_password_strength(password):
    if len(password) < 8:
        return 'La contraseña debe tener al menos 8 caracteres.'
    if not re.search(r'[A-Z]', password):
        return 'La contraseña debe contener al menos una letra mayúscula.'
    if not re.search(r'[a-z]', password):
        return 'La contraseña debe contener al menos una letra minúscula.'
    if not re.search(r'\d', password):
        return 'La contraseña debe contener al menos un número.'
    if not re.search(r'[^A-Za-z0-9]', password):
        return 'La contraseña debe contener al menos un carácter especial.'
    return None

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'myapp/signup.html', {'error': 'El correo electrónico no es válido'})
        if User.objects.filter(username=username).exists():
            return render(request, 'myapp/signup.html', {'error': 'El usuario ya existe'})
        if User.objects.filter(email=email).exists():
            return render(request, 'myapp/signup.html', {'error': 'El correo electrónico ya está registrado'})
        password_error = validate_password_strength(password)
        if password_error:
            return render(request, 'myapp/signup.html', {'error': password_error})
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False
        user.save()
        # Enviar email de activación
        current_site = get_current_site(request)
        subject = 'Activa tu cuenta en SugoiAnime'
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"http://{current_site.domain}/activar/{uid}/{token}/"
        message = render_to_string('myapp/activation_email.html', {
            'user': user,
            'activation_link': activation_link,
        })
        send_mail(subject, message, 'noreply@sugoianime.com', [user.email], fail_silently=False)
        return render(request, 'myapp/signup.html', {'success': 'Revisa tu correo para activar tu cuenta.'})
    return render(request, 'myapp/signup.html')

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return render(request, 'myapp/activation_invalid.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@staff_member_required
def contenido_list(request):
    contenidos = Contenido.objects.all()
    return render(request, 'myapp/contenido_list.html', {'contenidos': contenidos})

@staff_member_required
def contenido_create(request):
    if request.method == 'POST':
        form = ContenidoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('contenido_list')
    else:
        form = ContenidoForm()
    return render(request, 'myapp/contenido_form.html', {'form': form, 'accion': 'Crear'})

@staff_member_required
def contenido_update(request, pk):
    contenido = Contenido.objects.get(pk=pk)
    if request.method == 'POST':
        form = ContenidoForm(request.POST, request.FILES, instance=contenido)
        if form.is_valid():
            form.save()
            return redirect('contenido_list')
    else:
        form = ContenidoForm(instance=contenido)
    return render(request, 'myapp/contenido_form.html', {'form': form, 'accion': 'Editar'})

@staff_member_required
def contenido_delete(request, pk):
    contenido = Contenido.objects.get(pk=pk)
    if request.method == 'POST':
        contenido.delete()
        return redirect('contenido_list')
    return render(request, 'myapp/contenido_confirm_delete.html', {'contenido': contenido})

def password_reset_request(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        User = get_user_model()
        try:
            user = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            return render(request, 'myapp/password_reset_request.html', {'error': 'Usuario o email incorrecto'})
        current_site = get_current_site(request)
        subject = 'Recupera tu contraseña en SugoiAnime'
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://{current_site.domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
        message = render_to_string('myapp/password_reset_email.html', {
            'user': user,
            'reset_link': reset_link,
        })
        send_mail(subject, message, 'noreply@sugoianime.com', [user.email], fail_silently=False)
        return render(request, 'myapp/password_reset_request.html', {'success': 'Revisa tu correo para restablecer tu contraseña.'})
    return render(request, 'myapp/password_reset_request.html')


def password_reset_confirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            if password1 != password2:
                return render(request, 'myapp/password_reset_confirm.html', {'validlink': True, 'error': 'Las contraseñas no coinciden.'})
            password_error = validate_password_strength(password1)
            if password_error:
                return render(request, 'myapp/password_reset_confirm.html', {'validlink': True, 'error': password_error})
            user.set_password(password1)
            user.save()
            # Notificar por correo el cambio
            subject = 'Tu contraseña ha sido cambiada en SugoiAnime'
            message = render_to_string('myapp/password_changed_email.html', {'user': user})
            send_mail(subject, message, 'noreply@sugoianime.com', [user.email], fail_silently=False)
            return render(request, 'myapp/password_reset_complete.html')
        return render(request, 'myapp/password_reset_confirm.html', {'validlink': True})
    else:
        return render(request, 'myapp/password_reset_confirm.html', {'validlink': False})