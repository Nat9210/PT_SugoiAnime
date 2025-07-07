import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import ContenidoForm, UserUpdateForm, PerfilUpdateForm, EpisodioForm
from .models import (Contenido, Categoria, Episodio, ContenidoCategoria, Perfil, 
                     HistorialReproduccion, Favorito, Calificacion, AuditLog)
from .recommendations import obtener_recomendaciones_para_perfil, obtener_recomendaciones_por_categoria, obtener_contenido_similar
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
from django.forms import modelformset_factory
import re
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
import logging

# Logger para vistas
logger = logging.getLogger('myapp.views')

def get_client_ip(request):
    """Función auxiliar para obtener la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Vista principal
@login_required
def index(request):    # Contenido reciente
    contenidos_recientes = Contenido.objects.all().order_by('-id')[:8]
    
    # Recomendaciones personalizadas si el usuario tiene perfil
    recomendaciones_personalizadas = []
    perfil = request.user.perfiles.first() if request.user.is_authenticated else None
    
    if perfil:
        recomendaciones_personalizadas = obtener_recomendaciones_para_perfil(perfil, limite=8)
    
    # Contenido popular (más reproducido)
    contenido_popular = Contenido.objects.annotate(
        total_reproducciones=Count('historialreproduccion')
    ).filter(
        total_reproducciones__gt=0
    ).order_by('-total_reproducciones')[:6]
    
    # Categorías más populares
    categorias_populares = Categoria.objects.annotate(
        total_contenido=Count('contenidos')
    ).filter(
        total_contenido__gt=0
    ).order_by('-total_contenido')[:6]
    
    # Términos más buscados (basado en historial de búsqueda)
    from .models import HistorialBusqueda
    terminos_mas_buscados = HistorialBusqueda.obtener_mas_buscados(limite=8, dias=30)
      # Contenido más buscado basado en los términos populares
    contenido_mas_buscado = []
    if terminos_mas_buscados:
        # Obtener contenido que coincida con los términos más buscados
        for termino_data in terminos_mas_buscados[:6]:
            termino = termino_data['termino_normalizado']
            contenidos_relacionados = Contenido.objects.filter(
                Q(titulo__icontains=termino) | 
                Q(descripcion__icontains=termino) | 
                Q(categorias__nombre__icontains=termino)
            ).distinct()[:3]
            for contenido in contenidos_relacionados:
                if contenido not in contenido_mas_buscado:
                    contenido_mas_buscado.append(contenido)
                if len(contenido_mas_buscado) >= 8:
                    break
            if len(contenido_mas_buscado) >= 8:
                break
    
    # Contenido más visto (con rating promedio y cantidad de reproducciones)
    from django.db.models import Avg
    contenido_mas_visto = Contenido.objects.annotate(
        total_reproducciones=Count('historialreproduccion'),
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion')
    ).filter(
        total_reproducciones__gt=0
    ).order_by('-total_reproducciones')[:8]
      # Contenido con más me gusta (calificaciones 5)
    contenido_mas_gustado = Contenido.objects.annotate(
        total_likes=Count('calificacion', filter=Q(calificacion__calificacion=5)),
        total_dislikes=Count('calificacion', filter=Q(calificacion__calificacion=1)),
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion')
    ).filter(
        total_likes__gt=0
    ).order_by('-total_likes', '-rating_promedio')[:8]      # Contenido mejor valorado (por rating promedio)
    contenido_mejor_valorado = Contenido.objects.annotate(
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion'),
        total_likes=Count('calificacion', filter=Q(calificacion__calificacion=5))
    ).filter(
        total_calificaciones__gte=3  # Al menos 3 calificaciones para ser considerado
    ).order_by('-rating_promedio', '-total_calificaciones')[:8]
    
    # Contenido destacado para hero slider (mejor valorado + popular)
    contenido_destacado = Contenido.objects.annotate(
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion'),
        total_reproducciones=Count('historialreproduccion'),
        score_combinado=(
            Avg('calificacion__calificacion') * 0.6 + 
            Count('historialreproduccion') * 0.0001 +  # Factor pequeño para popularidad
            Count('calificacion') * 0.01  # Factor pequeño para cantidad de reviews
        )
    ).filter(
        rating_promedio__gte=4.0,  # Solo contenido bien valorado
        total_calificaciones__gte=1,
        imagen_portada__isnull=False  # Solo contenido con imagen
    ).order_by('-score_combinado', '-rating_promedio')[:4]
    
    # Si no hay suficiente contenido bien valorado, rellenar con popular
    if len(contenido_destacado) < 4:
        contenido_adicional = Contenido.objects.annotate(
            total_reproducciones=Count('historialreproduccion')
        ).filter(
            imagen_portada__isnull=False
        ).exclude(
            id__in=[c.id for c in contenido_destacado]
        ).order_by('-total_reproducciones')[:4-len(contenido_destacado)]
        
        contenido_destacado = list(contenido_destacado) + list(contenido_adicional)
    
    # Contenido agregado recientemente (últimos añadidos por fecha de creación)
    contenido_agregado_recientemente = Contenido.objects.filter(
        imagen_portada__isnull=False
    ).order_by('-id')[:6]
    
    # Contenido de Live Action (películas principalmente)
    contenido_live_action = Contenido.objects.filter(
        tipo='pelicula',
        imagen_portada__isnull=False
    ).annotate(
        total_reproducciones=Count('historialreproduccion')
    ).order_by('-total_reproducciones', '-id')[:6]
    
    # Si no hay suficientes películas, agregar series
    if len(contenido_live_action) < 6:
        contenido_adicional_live = Contenido.objects.filter(
            imagen_portada__isnull=False
        ).exclude(
            id__in=[c.id for c in contenido_live_action]
        ).order_by('-id')[:6-len(contenido_live_action)]
        contenido_live_action = list(contenido_live_action) + list(contenido_adicional_live)
    
    # Contenido más visto (sidebar)
    contenido_sidebar_mas_visto = Contenido.objects.annotate(
        total_reproducciones=Count('historialreproduccion')
    ).filter(
        total_reproducciones__gt=0,
        imagen_portada__isnull=False
    ).order_by('-total_reproducciones')[:4]
    
    # Nuevo contenido (sidebar) - similar a recientes pero limitado
    nuevo_contenido_sidebar = Contenido.objects.filter(
        imagen_portada__isnull=False
    ).order_by('-id')[:4]
    
    context = {
        'contenidos_recientes': contenidos_recientes,
        'recomendaciones_personalizadas': recomendaciones_personalizadas,
        'contenido_popular': contenido_popular,
        'categorias_populares': categorias_populares,
        'contenido_mas_buscado': contenido_mas_buscado,
        'contenido_mas_visto': contenido_mas_visto,
        'contenido_mas_gustado': contenido_mas_gustado,
        'contenido_mejor_valorado': contenido_mejor_valorado,
        'contenido_destacado': contenido_destacado,
        'contenido_agregado_recientemente': contenido_agregado_recientemente,
        'contenido_live_action': contenido_live_action,
        'contenido_sidebar_mas_visto': contenido_sidebar_mas_visto,
        'nuevo_contenido_sidebar': nuevo_contenido_sidebar,
        'terminos_mas_buscados': terminos_mas_buscados,
        'tiene_perfil': bool(perfil),
        'contenido_agregado_recientemente': contenido_agregado_recientemente,
        'contenido_live_action': contenido_live_action,
        'contenido_sidebar_mas_visto': contenido_sidebar_mas_visto,
        'nuevo_contenido_sidebar': nuevo_contenido_sidebar
    }
    
    return render(request, 'myapp/index.html', context)

# Vista detalle de contenido
@login_required
def render_anime_details(request):
    return render(request, 'myapp/anime-details.html')

# Vista de reproducción de contenido
@login_required
def render_anime_watching(request):
    return render(request, 'myapp/anime-watching.html')

# Vista de blog y detalles del blog, sin función
@login_required
def render_blog_details(request):
    return render(request, 'myapp/blog-details.html')

# Vista de blog, sin función
@login_required
def render_blog(request):
    return render(request, 'myapp/blog.html')

# Vistas de login y signup, sin conexión a la base de datos
def render_login(request):
    return render(request, 'myapp/login.html')

def render_signup(request):
    return render(request, 'myapp/signup.html')

# vistas renderizadas con conexión a la base de datos

# Vista para renderizar categorías con filtrado y ordenamiento
@login_required
def render_categories(request):
    cat_id = request.GET.get('cat')
    tipo = request.GET.get('tipo')
    
    # Parámetros de ordenamiento separados
    orden_titulo = request.GET.get('orden_titulo') 
    orden_año = request.GET.get('orden_año')
    
    qs = Contenido.objects.all()
    
    # Filtros
    if cat_id:
        qs = qs.filter(categorias__id=cat_id)
    if tipo:
        qs = qs.filter(tipo=tipo)

    # Orden dinámico
    order_fields = []

    # Orden por título
    if orden_titulo == 'asc':
        order_fields.append('titulo')
    elif orden_titulo == 'desc':
        order_fields.append('-titulo')

    # Orden por año
    if orden_año == 'asc':
        order_fields.append('año')  
    elif orden_año == 'desc':
        order_fields.append('-año')
    
    # Aplicar ordenamiento
    if order_fields:
        qs = qs.order_by(*order_fields)
    else:
        qs = qs.order_by('-id')  # lo más reciente por defecto

    categorias = Categoria.objects.all()
    return render(request, 'myapp/categories.html', {
        'contenidos': qs, 
        'categorias': categorias,
        'orden_titulo': orden_titulo,  
        'orden_año': orden_año
    })

# Vista del catálogo
@login_required
def render_catalogo(request):
    return render(request, 'myapp/catalogo.html')

#vistas conectadas a la base de datos
## Vista del perfil del usuario
@login_required 
def perfil_view(request):
    user = request.user
    seccion = request.GET.get('seccion', 'datos')
    perfil = user.perfiles.first()
    
    if not perfil:        # Si el usuario no tiene perfil, crear uno por defecto
        perfil = Perfil.objects.create(usuario=user, nombre=user.username, tipo='adulto')

    user_form = UserUpdateForm(instance=user)
    perfil_form = PerfilUpdateForm(instance=perfil)
    contenidos = None
    favoritos = None
    
    # Estadísticas para la sección admin
    total_usuarios = None
    total_contenido = None
    total_reproducciones = None
    total_logs = None
    
    if seccion == 'gestion' and user.is_staff: # solo admin.
        from django.db.models import Avg
        contenidos = Contenido.objects.annotate(
            total_likes=Count('calificacion', filter=Q(calificacion__calificacion=5)),
            total_dislikes=Count('calificacion', filter=Q(calificacion__calificacion=1)),
            rating_promedio=Avg('calificacion__calificacion')
        )
        
        # Funcionalidad de búsqueda simple
        search_query = request.GET.get('search', '')
        if search_query:
            contenidos = contenidos.filter(
                Q(titulo__icontains=search_query) |
                Q(descripcion__icontains=search_query)
            )
        
        # Filtro por tipo
        tipo_filter = request.GET.get('tipo', '')
        if tipo_filter:
            contenidos = contenidos.filter(tipo=tipo_filter)
        
        contenidos = contenidos.order_by('-fecha_importacion')
    
    elif seccion == 'admin' and user.is_staff:
        # Obtener estadísticas del sistema para la sección admin
        from django.contrib.auth.models import User
        total_usuarios = User.objects.count()
        total_contenido = Contenido.objects.count()
        total_reproducciones = HistorialReproduccion.objects.count()
        total_logs = AuditLog.objects.count()
    
    if seccion == 'favoritos':
        favoritos = Favorito.objects.filter(perfil=perfil).select_related('contenido').order_by('-fecha_agregado')

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
        'favoritos': favoritos,
        'search_query': request.GET.get('search', ''),
        'tipo_filter': request.GET.get('tipo', ''),
        'total_usuarios': total_usuarios,
        'total_contenido': total_contenido,
        'total_reproducciones': total_reproducciones,
        'total_logs': total_logs,
    })

# Función para manejar la vista de inicio de sesión
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

# Validacion de contraseña
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

# Función para manejar la vista de registro de nuevos usuarios
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
        user.is_active =  False  # El usuario INACTIVO hasta confirmacion con email
        user.save()
        
        # Enviar email de activación
        current_site = get_current_site(request)
        subject = 'Activa tu cuenta en SugoiAnime'
        # token de activación de nuevo usuario
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        # link para activar la cuenta
        activation_link = f"http://{current_site.domain}/activar/{uid}/{token}/" # URL de activación unica
        message = render_to_string('myapp/activation_email.html', {
            'user': user,
            'activation_link': activation_link,
        })
        send_mail(subject, message, 'noreply@sugoianime.com', [user.email], fail_silently=False)
        return render(request, 'myapp/signup.html', {'success': 'Revisa tu correo para activar tu cuenta.'})
    return render(request, 'myapp/signup.html')

# Función para activar la cuenta del usuario
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    # Verificar el token de activación
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True # ACTIVA la cuenta del usuario
        user.save()
        return redirect('login')
    else:
        return render(request, 'myapp/activation_invalid.html')

# Función para cerrar sesión
def logout_view(request):
    logout(request)
    return redirect('login')

# FUNCIÓN ELIMINADA: contenido_list - Ver FUNCIONES_DEPRECADAS.md para detalles
# Reemplazada por: /perfil/?seccion=gestion
# Fecha de eliminación: 6 de julio de 2025

@staff_member_required
def contenido_create(request):
    if request.method == 'POST':
        form = ContenidoForm(request.POST, request.FILES)
        if form.is_valid():
            contenido = form.save()
            if contenido.tipo == 'serie':
                # Redirigir a una vista para agregar episodios
                return redirect('agregar_episodios', contenido_id=contenido.id)
            return HttpResponseRedirect('/perfil/?seccion=gestion')
    else:
        form = ContenidoForm()
    return render(request, 'myapp/contenido_form.html', {'form': form, 'accion': 'Crear'})

@staff_member_required
def agregar_episodios(request, contenido_id):
    contenido = Contenido.objects.get(pk=contenido_id)
    EpisodioFormSet = modelformset_factory(Episodio, form=EpisodioForm, extra=1, can_delete=True)
    queryset = Episodio.objects.filter(serie=contenido)
    mensaje = None
    if request.method == 'POST':
        formset = EpisodioFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            episodios = formset.save(commit=False)
            for episodio in episodios:
                episodio.serie = contenido
                episodio.save()
            for obj in formset.deleted_objects:
                obj.delete()
            mensaje = 'Capítulo(s) agregado(s) exitosamente.'
            formset = EpisodioFormSet(queryset=Episodio.objects.filter(serie=contenido))
            return render(request, 'myapp/episodios_form.html', {'formset': formset, 'contenido': contenido, 'mensaje': mensaje})
    else:
        formset = EpisodioFormSet(queryset=queryset)
    return render(request, 'myapp/episodios_form.html', {'formset': formset, 'contenido': contenido, 'mensaje': mensaje})

@staff_member_required
def contenido_update(request, pk):
    contenido = Contenido.objects.get(pk=pk)
    if request.method == 'POST':
        form = ContenidoForm(request.POST, request.FILES, instance=contenido)
        if form.is_valid():
            form.save()
            # Redirigir siempre al perfil con la sección de gestión
            return HttpResponseRedirect('/perfil/?seccion=gestion')
    else:
        form = ContenidoForm(instance=contenido)
    return render(request, 'myapp/contenido_form.html', {'form': form, 'accion': 'Editar'})

@staff_member_required
def contenido_delete(request, pk):
    contenido = Contenido.objects.get(pk=pk)
    if request.method == 'POST':
        contenido.delete()
        return HttpResponseRedirect('/perfil/?seccion=gestion')
    return render(request, 'myapp/contenido_confirm_delete.html', {'contenido': contenido})

# Función de solicitud el restablecimiento de contraseña
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
        # token de restablecimiento de contraseña
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://{current_site.domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
        
        message = render_to_string('myapp/password_reset_email.html', {
            'user': user,
            'reset_link': reset_link,
        })
        
        send_mail(subject, message, 'noreply@sugoianime.com', [user.email], fail_silently=False)
        return redirect('password_reset_done')
    
    return render(request, 'myapp/password_reset_request.html')

# Confirmación de restablecimiento de contraseña
def password_reset_confirm(request, uidb64, token):
    User = get_user_model()
    # Intentar decodificar el uidb64 para obtener el ID del usuario
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    # Si el usuario no existe o el token es inválido, mostrar un mensaje de error  
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None  
    # Verificar el token de restablecimiento de contraseña
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            # Si el token es válido, permitir al usuario restablecer su contraseña
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            # Validar que las contraseñas coincidan y sean fuertes
            if password1 != password2:
                return render(request, 'myapp/password_reset_confirm.html', 
                            {'validlink': True, 'error': 'Las contraseñas no coinciden.'})
            password_error = validate_password_strength(password1)
            # Validar la fortaleza de la contraseña
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

def anime_details(request, contenido_id):
    contenido = Contenido.objects.get(pk=contenido_id)
    es_favorito = False
    contenido_similar = []
    
    if request.user.is_authenticated:
        perfil = request.user.perfiles.first()
        if perfil:
            es_favorito = Favorito.objects.filter(perfil=perfil, contenido=contenido).exists()
            # Obtener contenido similar basado en el sistema de recomendaciones
            contenido_similar = obtener_contenido_similar(perfil, contenido, limite=6)
    
    # Si no hay usuario autenticado o no tiene recomendaciones personalizadas,
    # mostrar contenido similar basado solo en categorías
    if not contenido_similar:
        categorias_contenido = contenido.categorias.all()
        contenido_similar = Contenido.objects.filter(
            categorias__in=categorias_contenido
        ).exclude(
            id=contenido.id
        ).annotate(
            categorias_compartidas=Count('categorias', filter=Q(categorias__in=categorias_contenido))
        ).order_by('-categorias_compartidas', '?')[:6]
        contenido_similar = list(contenido_similar)
    
    context = {
        'contenido': contenido, 
        'es_favorito': es_favorito,
        'contenido_similar': contenido_similar
    }
    
    return render(request, 'myapp/anime-details.html', context)

@login_required
def contenido_gestion_episodios(request, contenido_id):
    contenido = get_object_or_404(Contenido, pk=contenido_id)
    episodios = Episodio.objects.filter(serie=contenido)
    return render(request, 'myapp/episodios_form.html', {'contenido': contenido, 'episodios': episodios})

@staff_member_required
def episodio_create(request, contenido_id):
    contenido = get_object_or_404(Contenido, pk=contenido_id)
    if request.method == 'POST':
        form = EpisodioForm(request.POST)
        if form.is_valid():
            episodio = form.save(commit=False)
            episodio.serie = contenido
            episodio.save()
            messages.success(request, 'Episodio creado exitosamente.')
            return redirect('contenido_gestion_episodios', contenido_id=contenido.id)
    else:
        form = EpisodioForm()
    return render(request, 'myapp/episodio_form.html', {'form': form, 'contenido': contenido, 'accion': 'Agregar'})

@staff_member_required
def episodio_update(request, episodio_id):
    episodio = get_object_or_404(Episodio, pk=episodio_id)
    contenido = episodio.serie
    if request.method == 'POST':
        form = EpisodioForm(request.POST, instance=episodio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Episodio editado exitosamente.')
            return redirect('contenido_gestion_episodios', contenido_id=contenido.id)
    else:
        form = EpisodioForm(instance=episodio)
    return render(request, 'myapp/episodio_form.html', {'form': form, 'contenido': contenido, 'accion': 'Editar'})

@staff_member_required
def episodio_delete(request, episodio_id):
    episodio = get_object_or_404(Episodio, pk=episodio_id)
    contenido_id = episodio.serie.id
    if request.method == 'POST':
        episodio.delete()
        messages.success(request, 'Episodio eliminado exitosamente.')
        return redirect('contenido_gestion_episodios', contenido_id=contenido_id)
    return render(request, 'myapp/episodio_confirm_delete.html', {'episodio': episodio})

@login_required
def anime_watching(request, episodio_id):
    # OPTIMIZACIÓN: Usar select_related para evitar consultas adicionales
    episodio = Episodio.objects.select_related('serie').prefetch_related('serie__categorias').get(pk=episodio_id)
    contenido = episodio.serie
    user = request.user
    perfil = user.perfiles.first()  # Se asume un perfil por usuario
    
    # Registrar reproducción en logs de auditoría (optimizado)
    AuditLog.log_action(
        accion='PLAY',
        descripcion=f"Episodio: {contenido.titulo} - {episodio.titulo}",
        usuario=user,
        perfil=perfil,
        tabla_afectada='Episodio',
        objeto_id=episodio_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],  # Limitar tamaño
        datos_adicionales={
            'tipo': 'episodio',
            'temporada': episodio.temporada,
            'numero': episodio.numero_episodio
        }
    )
    
    if perfil:
        # OPTIMIZACIÓN: Usar get_or_create para evitar consultas adicionales
        HistorialReproduccion.objects.get_or_create(
            perfil=perfil,
            contenido=contenido,
            episodio=episodio,
            defaults={'tiempo_reproducido': 0}
        )
        
        # OPTIMIZACIÓN: Obtener todos los episodios vistos de una vez
        episodios_vistos = list(
            HistorialReproduccion.objects.filter(perfil=perfil, contenido=contenido)
            .exclude(episodio=None)
            .values_list('episodio_id', flat=True)
        )
    else:
        episodios_vistos = []
    
    # OPTIMIZACIÓN: Headers de cache para recursos estáticos
    response = render(request, 'myapp/anime-watching.html', {
        'episodio': episodio,
        'contenido': contenido,
        'episodios_vistos': episodios_vistos
    })
    
    # Cache de página por 5 minutos (solo para contenido que no cambia frecuentemente)
    response['Cache-Control'] = 'max-age=300, must-revalidate'
    response['ETag'] = f'"episode-{episodio.id}-{episodio.video_url}"'
    
    # Hint para precargar el próximo episodio
    next_episode = Episodio.objects.filter(
        serie=contenido, 
        numero_episodio=episodio.numero_episodio + 1
    ).first()
    if next_episode:
        response['Link'] = f'</static/myapp/css/video-optimizations.css>; rel=preload; as=style'
    
    return response

@login_required
def movie_watching(request, contenido_id):
    """Vista para reproducir películas - OPTIMIZADA"""
    # OPTIMIZACIÓN: Usar select_related y prefetch_related
    contenido = get_object_or_404(
        Contenido.objects.select_related().prefetch_related('categorias'), 
        pk=contenido_id, 
        tipo='pelicula'
    )
    user = request.user
    perfil = user.perfiles.first()  # Se asume un perfil por usuario
    
    # Registrar reproducción en logs de auditoría (optimizado)
    AuditLog.log_action(
        accion='PLAY',
        descripcion=f"Película: {contenido.titulo}",
        usuario=user,
        perfil=perfil,
        tabla_afectada='Contenido',
        objeto_id=contenido_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],  # Limitar tamaño
        datos_adicionales={
            'tipo': 'pelicula',
            'duracion': contenido.duracion
        }
    )
    
    if perfil:
        # OPTIMIZACIÓN: Usar get_or_create para evitar consultas adicionales
        HistorialReproduccion.objects.get_or_create(
            perfil=perfil,
            contenido=contenido,
            episodio=None,  # Las películas no tienen episodios
            defaults={'tiempo_reproducido': 0}
        )
    
    # Renderizar el template unificado (mismo que para episodios)
    response = render(request, 'myapp/anime-watching.html', {
        'contenido': contenido,
        'episodio': None,  # Para películas no hay episodio
    })
    
    # OPTIMIZACIÓN: Cache más agresivo para películas (no cambian frecuentemente)
    response['Cache-Control'] = 'max-age=600, public'  # 10 minutos
    response['ETag'] = f'"movie-{contenido.id}-{contenido.video_url}"'
    
    return response

@login_required
@require_POST
def toggle_favorito(request):
    contenido_id = request.POST.get('contenido_id')
    user = request.user
    perfil = user.perfiles.first()
    if not perfil or not contenido_id:
        return JsonResponse({'success': False, 'error': 'Perfil o contenido no encontrado'})
    
    contenido = get_object_or_404(Contenido, pk=contenido_id)
    favorito, created = Favorito.objects.get_or_create(perfil=perfil, contenido=contenido)
    
    if not created:
        favorito.delete()
        accion = 'UNFAVORITE'
        descripcion = f"Contenido removido de favoritos: {contenido.titulo}"
        is_favorito = False
    else:
        accion = 'FAVORITE'
        descripcion = f"Contenido agregado a favoritos: {contenido.titulo}"
        is_favorito = True
    
    # Registrar acción en logs de auditoría
    AuditLog.log_action(
        accion=accion,
        descripcion=descripcion,
        usuario=user,
        perfil=perfil,
        tabla_afectada='Favorito',
        objeto_id=contenido_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),        datos_adicionales={
            'contenido_id': contenido_id,
            'contenido_titulo': contenido.titulo,
            'contenido_tipo': contenido.tipo
        }
    )
    
    return JsonResponse({'success': True, 'favorito': is_favorito})

def busqueda(request):
    query = request.GET.get('q', '').strip()
    resultados = []
    
    if query:
        # Búsqueda optimizada con índices
        tipo = None
        if query.lower() in ['serie', 'series']:
            tipo = 'serie'
        elif query.lower() in ['pelicula', 'películas', 'peliculas', 'movie', 'movies']:
            tipo = 'pelicula'
        
        # Construir filtros de búsqueda optimizados
        filtros = Q(titulo__icontains=query) | Q(descripcion__icontains=query) | Q(categorias__nombre__icontains=query)
        if tipo:
            filtros = filtros | Q(tipo=tipo)
        
        # Optimizar consulta con prefetch_related y select_related
        resultados = Contenido.objects.filter(filtros).prefetch_related('categorias').distinct().order_by('-año', '-id')
        
        # Limitar resultados para mejor rendimiento
        resultados = resultados[:50]  # Máximo 50 resultados
        
        # Registrar búsqueda en historial y logs de auditoría
        if request.user.is_authenticated:
            perfil = request.user.perfiles.first()
            
            # Registrar en historial de búsqueda
            from .models import HistorialBusqueda
            HistorialBusqueda.registrar_busqueda(
                termino=query,
                usuario=request.user,
                perfil=perfil,
                resultados_count=len(resultados),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Registrar en logs de auditoría
            AuditLog.log_action(
                accion='SEARCH',
                descripcion=f"Búsqueda realizada: '{query}' - {len(resultados)} resultados",
                usuario=request.user,
                perfil=perfil,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                datos_adicionales={
                    'query': query,
                    'query_length': len(query),
                    'results_count': len(resultados),
                    'has_results': len(resultados) > 0
                }
            )
    
    return render(request, 'myapp/busqueda.html', {'query': query, 'resultados': resultados})

# VISTA DE ESTADÍSTICAS DEL SISTEMA DE RECOMENDACIONES
@staff_member_required
def estadisticas_recomendaciones(request):
    """Vista para mostrar estadísticas del sistema de recomendaciones"""
    # Estadísticas generales
    total_usuarios = User.objects.count()
    total_perfiles = Perfil.objects.count()
    total_contenido = Contenido.objects.count()
    total_reproducciones = HistorialReproduccion.objects.count()
    total_calificaciones = Calificacion.objects.count()
    total_favoritos = Favorito.objects.count()
    # Usuarios más activos
    usuarios_activos = Perfil.objects.annotate(
        total_actividad=Count('historialreproduccion') + 
                        Count('calificacion') + 
                        Count('favorito')
    ).filter(total_actividad__gt=0).order_by('-total_actividad')[:10]
    # Contenido más popular
    contenido_popular = Contenido.objects.annotate(
        total_interacciones=Count('historialreproduccion') + 
                            Count('calificacion') + 
                            Count('favorito')
    ).filter(total_interacciones__gt=0).order_by('-total_interacciones')[:10]
    # Categorías más populares
    categorias_populares = Categoria.objects.annotate(
        total_interacciones=Count('contenidos__historialreproduccion') + 
                            Count('contenidos__calificacion') + 
                            Count('contenidos__favorito')
    ).filter(total_interacciones__gt=0).order_by('-total_interacciones')[:10]    # Calificaciones promedio
    likes = Calificacion.objects.filter(calificacion=5).count()
    dislikes = Calificacion.objects.filter(calificacion=1).count()
    neutrales = Calificacion.objects.filter(calificacion__in=[2, 3, 4]).count()
    
    context = {
        'total_usuarios': total_usuarios,
        'total_perfiles': total_perfiles,
        'total_contenido': total_contenido,
        'total_reproducciones': total_reproducciones,
        'total_calificaciones': total_calificaciones,
        'total_favoritos': total_favoritos,
        'usuarios_activos': usuarios_activos,
        'contenido_popular': contenido_popular,
        'categorias_populares': categorias_populares,
        'likes': likes,
        'dislikes': dislikes,
        'neutrales': neutrales,
        'total_interacciones': total_reproducciones + total_calificaciones + total_favoritos
    }
    
    return render(request, 'myapp/estadisticas_recomendaciones.html', context)

# SISTEMA DE RATING/LIKE-DISLIKE
@login_required
@require_POST
def toggle_like(request):
    """Función para dar like a un contenido usando el modelo Calificacion con calificación 5"""
    contenido_id = request.POST.get('contenido_id')
    user = request.user
    perfil = user.perfiles.first()
    
    if not perfil or not contenido_id:
        return JsonResponse({'success': False, 'error': 'Perfil o contenido no encontrado'})
    
    contenido = get_object_or_404(Contenido, pk=contenido_id)
    
    # Buscar si ya existe un comentario/rating de este usuario para este contenido
    comentario_existente = Calificacion.objects.filter(perfil=perfil, contenido=contenido).first()
    
    if comentario_existente:
        # Si ya existe y es un like (calificación 5), lo removemos (toggle off)
        if comentario_existente.calificacion == 5:
            comentario_existente.delete()
            return JsonResponse({'success': True, 'liked': False, 'disliked': False})
        else:
            # Si era un dislike, lo cambiamos a like
            comentario_existente.calificacion = 5
            comentario_existente.save()
            return JsonResponse({'success': True, 'liked': True, 'disliked': False})
    else:
        # Crear nuevo like
        Calificacion.objects.create(
            perfil=perfil,
            contenido=contenido,
            calificacion=5
        )
        return JsonResponse({'success': True, 'liked': True, 'disliked': False})

@login_required
@require_POST
def toggle_dislike(request):
    """Función para dar dislike a un contenido usando el modelo Calificacion con calificación 1"""
    contenido_id = request.POST.get('contenido_id')
    user = request.user
    perfil = user.perfiles.first()
    
    if not perfil or not contenido_id:
        return JsonResponse({'success': False, 'error': 'Perfil o contenido no encontrado'})
    
    contenido = get_object_or_404(Contenido, pk=contenido_id)
    
    # Buscar si ya existe un comentario/rating de este usuario para este contenido
    comentario_existente = Calificacion.objects.filter(perfil=perfil, contenido=contenido).first()
    
    if comentario_existente:
        # Si ya existe y es un dislike (calificación 1), lo removemos (toggle off)
        if comentario_existente.calificacion == 1:
            comentario_existente.delete()
            return JsonResponse({'success': True, 'liked': False, 'disliked': False})
        else:
            # Si era un like, lo cambiamos a dislike
            comentario_existente.calificacion = 1
            comentario_existente.save()
            return JsonResponse({'success': True, 'liked': False, 'disliked': True})
    else:
        # Crear nuevo dislike
        Calificacion.objects.create(
            perfil=perfil,
            contenido=contenido,
            calificacion=1
        )
        return JsonResponse({'success': True, 'liked': False, 'disliked': True})

@login_required
def get_user_rating(request, contenido_id):
    """Función para obtener el rating actual del usuario para un contenido específico"""
    user = request.user
    perfil = user.perfiles.first()
    
    if not perfil:
        return JsonResponse({'success': False, 'error': 'Perfil no encontrado'})
    
    contenido = get_object_or_404(Contenido, pk=contenido_id)
    comentario = Calificacion.objects.filter(perfil=perfil, contenido=contenido).first()
    
    if comentario:
        if comentario.calificacion == 5:
            return JsonResponse({'success': True, 'liked': True, 'disliked': False})
        elif comentario.calificacion == 1:
            return JsonResponse({'success': True, 'liked': False, 'disliked': True})
        else:
            return JsonResponse({'success': True, 'liked': False, 'disliked': False})
    else:
        return JsonResponse({'success': True, 'liked': False, 'disliked': False})

def get_content_ratings(request, contenido_id):
    """Función para obtener estadísticas de rating de un contenido"""
    contenido = get_object_or_404(Contenido, pk=contenido_id)
      # Contar likes (calificación 5) y dislikes (calificación 1)
    likes = Calificacion.objects.filter(contenido=contenido, calificacion=5).count()
    dislikes = Calificacion.objects.filter(contenido=contenido, calificacion=1).count()
    
    return JsonResponse({
        'success': True, 
        'likes': likes, 
        'dislikes': dislikes,
        'total_ratings': likes + dislikes
    })

# SISTEMA DE RECOMENDACIONES
@login_required
def recomendaciones_personalizadas(request):
    """Vista principal de recomendaciones personalizadas"""
    perfil = request.user.perfiles.first()
    if not perfil:
        return redirect('perfil')
    
    # Obtener recomendaciones personalizadas
    recomendaciones = obtener_recomendaciones_para_perfil(perfil, limite=20)
      # Obtener categorías favoritas del usuario
    categorias_usuario = Categoria.objects.filter(
        Q(contenidos__historialreproduccion__perfil=perfil) |        Q(contenidos__favorito__perfil=perfil) |
        Q(contenidos__calificacion__perfil=perfil, contenidos__calificacion__calificacion=5)
    ).annotate(
        popularidad=Count('contenidos__historialreproduccion') + 
                   Count('contenidos__favorito') + 
                   Count('contenidos__calificacion')
    ).order_by('-popularidad')[:6]
    
    context = {
        'recomendaciones': recomendaciones,
        'categorias_usuario': categorias_usuario,
        'total_recomendaciones': len(recomendaciones)
    }
    
    return render(request, 'myapp/recomendaciones.html', context)

@login_required
def recomendaciones_categoria(request, categoria_id):
    """Vista de recomendaciones por categoría específica"""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    perfil = request.user.perfiles.first()
    
    if not perfil:
        return redirect('perfil')
    
    # Obtener recomendaciones de la categoría
    recomendaciones = obtener_recomendaciones_por_categoria(perfil, categoria, limite=12)
    
    context = {
        'categoria': categoria,
        'recomendaciones': recomendaciones,
        'total_recomendaciones': len(recomendaciones)
    }
    
    return render(request, 'myapp/recomendaciones_categoria.html', context)

@login_required
def contenido_similar(request, contenido_id):
    """Vista de contenido similar a uno específico"""
    try:
        contenido = get_object_or_404(Contenido, pk=contenido_id)
        perfil = request.user.perfiles.first()
        
        if not perfil:
            return redirect('perfil')
        
        # Obtener contenido similar
        similar = obtener_contenido_similar(perfil, contenido, limite=8)
        
        # Filtrar objetos que no tengan ID válido
        similar_valido = [item for item in similar if item and hasattr(item, 'id') and item.id]
        
        context = {
            'contenido_original': contenido,
            'contenido_similar': similar_valido,
            'total_similar': len(similar_valido)
        }
        
        return render(request, 'myapp/contenido_similar.html', context)
        
    except Exception as e:
        # Log del error para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en contenido_similar: {e}")
        
        # Redirigir a la página principal en caso de error
        messages.error(request, "Error al cargar contenido similar. Por favor, intenta de nuevo.")
        return redirect('index')

@login_required
def api_recomendaciones(request):
    """API endpoint para obtener recomendaciones vía AJAX"""
    perfil = request.user.perfiles.first()
    if not perfil:
        return JsonResponse({'success': False, 'error': 'Perfil no encontrado'})
    
    limite = int(request.GET.get('limite', 10))
    categoria_id = request.GET.get('categoria_id')
    
    if categoria_id:
        try:
            categoria = Categoria.objects.get(pk=categoria_id)
            recomendaciones = obtener_recomendaciones_por_categoria(perfil, categoria, limite)
        except Categoria.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Categoría no encontrada'})
    else:
        recomendaciones = obtener_recomendaciones_para_perfil(perfil, limite)
    
    # Convertir a JSON
    data = []
    for contenido in recomendaciones:
        data.append({
            'id': contenido.id,
            'titulo': contenido.titulo,
            'tipo': contenido.get_tipo_display(),
            'año': contenido.año,
            'imagen_url': contenido.imagen_portada.url if contenido.imagen_portada else None,
            'url_detalle': f'/anime/{contenido.id}/',
            'categorias': [cat.nombre for cat in contenido.categorias.all()]
        })
    
    return JsonResponse({
        'success': True,
        'recomendaciones': data,
        'total': len(data)
    })

# Vista que muestra confirmación de que se envió el email
def password_reset_done(request):
    return render(request, 'myapp/password_reset_done.html')

# Vista que muestra confirmación de que la contraseña fue cambiada exitosamente
def password_reset_complete(request):
    return render(request, 'myapp/password_reset_complete.html')