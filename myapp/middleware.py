from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.utils import timezone
from .models import AuditLog, SesionUsuario, AccesoFallido
import logging

# Logger para middleware
logger = logging.getLogger('myapp.audit')

class AuditMiddleware(MiddlewareMixin):
    """Middleware para registrar automáticamente las acciones de los usuarios"""
    
    def process_request(self, request):
        # Agregar información de IP y User-Agent al request para facilitar el logging
        request.audit_ip = self.get_client_ip(request)
        request.audit_user_agent = request.META.get('HTTP_USER_AGENT', '')
        return None
    
    def process_response(self, request, response):
        # Registrar acciones específicas basadas en la URL y método
        if hasattr(request, 'user') and request.user.is_authenticated:
            self.log_user_action(request, response)
        return response
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_user_action(self, request, response):
        """Registrar acciones específicas del usuario"""
        try:
            path = request.path
            method = request.method
            user = request.user
            perfil = getattr(request, 'perfil_activo', None)
            
            # Solo registrar para ciertas rutas importantes
            if self.should_log_path(path, method):
                accion, descripcion = self.get_action_description(path, method, request)
                
                if accion:
                    AuditLog.log_action(
                        accion=accion,
                        descripcion=descripcion,
                        usuario=user,
                        perfil=perfil,
                        ip_address=request.audit_ip,
                        user_agent=request.audit_user_agent,
                        datos_adicionales={
                            'path': path,
                            'method': method,
                            'status_code': response.status_code
                        }
                    )
        except Exception as e:
            logger.error(f"Error en AuditMiddleware: {str(e)}")
    
    def should_log_path(self, path, method):
        """Determinar si una ruta debe ser registrada"""
        # Rutas a registrar
        log_paths = [
            '/reproducir/',
            '/calificar/',
            '/favoritos/',
            '/buscar/',
            '/perfil/',
            '/admin/',
        ]
        
        # Registrar POST, PUT, DELETE de todas las rutas importantes
        if method in ['POST', 'PUT', 'DELETE']:
            return any(log_path in path for log_path in log_paths)
        
        # Registrar GET solo de ciertas rutas
        if method == 'GET':
            return any(log_path in path for log_path in ['/admin/', '/perfil/'])
        
        return False
    
    def get_action_description(self, path, method, request):
        """Obtener la acción y descripción basada en la ruta"""
        if '/reproducir/' in path:
            return 'PLAY', f"Reproducción de contenido - {path}"
        elif '/calificar/' in path:
            return 'RATE', f"Calificación de contenido - {method}"
        elif '/favoritos/' in path and method == 'POST':
            return 'FAVORITE', f"Agregado a favoritos"
        elif '/favoritos/' in path and method == 'DELETE':
            return 'UNFAVORITE', f"Removido de favoritos"
        elif '/buscar/' in path:
            query = request.GET.get('q', '')
            return 'SEARCH', f"Búsqueda realizada: '{query}'"
        elif '/admin/' in path:
            return 'VIEW', f"Acceso al panel de administración - {path}"
        elif '/perfil/' in path:
            return 'VIEW', f"Acceso/modificación de perfil - {method}"
        
        return None, None


# Receivers para eventos de autenticación
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registrar inicio de sesión exitoso"""
    try:
        # Crear sesión de usuario
        session_key = request.session.session_key
        if session_key:
            SesionUsuario.objects.create(
                usuario=user,
                session_key=session_key,
                ip_address=AuditMiddleware().get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        # Registrar en auditoría
        AuditLog.log_action(
            accion='LOGIN',
            descripcion=f"Inicio de sesión exitoso",
            usuario=user,
            ip_address=AuditMiddleware().get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            datos_adicionales={'session_key': session_key}
        )
        
    except Exception as e:
        logger.error(f"Error al registrar login: {str(e)}")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registrar cierre de sesión"""
    try:
        # Finalizar sesión de usuario
        session_key = request.session.session_key
        if session_key:
            try:
                sesion = SesionUsuario.objects.get(session_key=session_key, activa=True)
                sesion.fecha_fin = timezone.now()
                sesion.activa = False
                sesion.save()
            except SesionUsuario.DoesNotExist:
                pass
        
        # Registrar en auditoría
        if user:
            AuditLog.log_action(
                accion='LOGOUT',
                descripcion=f"Cierre de sesión",
                usuario=user,
                ip_address=AuditMiddleware().get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                datos_adicionales={'session_key': session_key}
            )
            
    except Exception as e:
        logger.error(f"Error al registrar logout: {str(e)}")

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Registrar intento de inicio de sesión fallido"""
    try:
        username = credentials.get('username', 'Desconocido')
        
        # Registrar acceso fallido
        AccesoFallido.objects.create(
            username=username,
            ip_address=AuditMiddleware().get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            motivo="Credenciales incorrectas"
        )
        
        # Registrar en auditoría
        AuditLog.log_action(
            accion='LOGIN',
            descripcion=f"Intento de inicio de sesión fallido para usuario: {username}",
            nivel='WARNING',
            ip_address=AuditMiddleware().get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            datos_adicionales={'attempted_username': username}
        )
        
    except Exception as e:
        logger.error(f"Error al registrar login fallido: {str(e)}")
