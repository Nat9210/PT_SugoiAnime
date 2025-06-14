from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import logging

# Configurar logger de auditoría
audit_logger = logging.getLogger('myapp.audit')

# Tabla de perfiles dentro de una cuenta de usuario
class Perfil(models.Model):
    TIPO_CHOICES = [
        ('adulto', 'Adulto'),
        ('infantil', 'Infantil'),
    ]

    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='perfiles')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"

# Tabla de categorías
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# Tabla de contenido (series y películas)
class Contenido(models.Model):
    TIPO_CHOICES = [
        ('serie', 'Serie'),
        ('pelicula', 'Película'),
    ]

    titulo = models.CharField(max_length=255, db_index=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, db_index=True)
    descripcion = models.TextField(blank=True)
    año = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    duracion = models.PositiveIntegerField(help_text="Duración en minutos", null=True, blank=True)
    idioma = models.CharField(max_length=50, blank=True)
    imagen_portada = models.ImageField(upload_to='portadas/', null=True, blank=True)
    video_url = models.URLField(max_length=1000, null=True, blank=True)
    categorias = models.ManyToManyField(Categoria, through='ContenidoCategoria', related_name='contenidos')

    class Meta:
        indexes = [
            models.Index(fields=['titulo', 'tipo']),
            models.Index(fields=['año', '-id']),
            models.Index(fields=['-id']),
        ]
        ordering = ['-id']

    def __str__(self):
        return self.titulo

# Relación entre contenido y categorías
class ContenidoCategoria(models.Model):
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

# Tabla de episodios (solo para series)
class Episodio(models.Model):
    serie = models.ForeignKey(Contenido, on_delete=models.CASCADE, limit_choices_to={'tipo': 'serie'})
    temporada = models.PositiveIntegerField()
    numero_episodio = models.PositiveIntegerField()
    titulo = models.CharField(max_length=255)
    duracion = models.PositiveIntegerField(help_text="Duración en minutos")
    video_url = models.URLField(max_length=1000, blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"T{self.temporada}E{self.numero_episodio} - {self.titulo}"
    
    @property
    def video_source(self):
        """Devuelve la fuente de video prioritaria"""
        if self.video_file and self.video_file.name:
            return self.video_file.url
        elif self.video_url:
            return self.video_url
        return ""

# Historial de reproducción por perfil
class HistorialReproduccion(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    episodio = models.ForeignKey(Episodio, on_delete=models.CASCADE, null=True, blank=True)
    tiempo_reproducido = models.PositiveIntegerField(help_text="Segundos")
    fecha = models.DateTimeField(auto_now_add=True)

# Favoritos por perfil
class Favorito(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

# Calificaciones por perfil
class Calificacion(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    calificacion = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.perfil.nombre} - {self.contenido.titulo} ({self.calificacion}⭐)"

# Modelo de Auditoría
class AuditLog(models.Model):
    ACCION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('VIEW', 'Ver'),
        ('LOGIN', 'Iniciar Sesión'),
        ('LOGOUT', 'Cerrar Sesión'),
        ('PLAY', 'Reproducir'),
        ('PAUSE', 'Pausar'),
        ('RATE', 'Calificar'),
        ('FAVORITE', 'Agregar a Favoritos'),
        ('UNFAVORITE', 'Quitar de Favoritos'),
        ('SEARCH', 'Buscar'),
        ('FILTER', 'Filtrar'),
    ]
    
    NIVEL_CHOICES = [
        ('INFO', 'Información'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Crítico'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    perfil = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES, db_index=True)
    tabla_afectada = models.CharField(max_length=100, blank=True)
    objeto_id = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField()
    nivel = models.CharField(max_length=10, choices=NIVEL_CHOICES, default='INFO')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    datos_adicionales = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'accion']),
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['perfil', 'timestamp']),
            models.Index(fields=['nivel', 'timestamp']),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else 'Anónimo'
        perfil_str = f" - {self.perfil.nombre}" if self.perfil else ""
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {usuario_str}{perfil_str} | {self.get_accion_display()}"

    @classmethod
    def log_action(cls, accion, descripcion, usuario=None, perfil=None, tabla_afectada='', 
                    objeto_id='', nivel='INFO', ip_address=None, user_agent='', datos_adicionales=None):
        """Método para registrar acciones de auditoría"""
        try:
            # Registrar en base de datos
            audit_entry = cls.objects.create(
                usuario=usuario,
                perfil=perfil,
                accion=accion,
                tabla_afectada=tabla_afectada,
                objeto_id=str(objeto_id) if objeto_id else '',
                descripcion=descripcion,
                nivel=nivel,
                ip_address=ip_address,
                user_agent=user_agent,
                datos_adicionales=datos_adicionales
            )
            
            # También registrar en archivo de log
            usuario_str = usuario.username if usuario else 'Anónimo'
            perfil_str = f" - Perfil: {perfil.nombre}" if perfil else ""
            log_message = f"Usuario: {usuario_str}{perfil_str} | Acción: {accion} | {descripcion}"
            
            if nivel == 'ERROR' or nivel == 'CRITICAL':
                audit_logger.error(log_message)
            elif nivel == 'WARNING':
                audit_logger.warning(log_message)
            else:
                audit_logger.info(log_message)
                
            return audit_entry
            
        except Exception as e:
            # Si falla el registro en BD, al menos registrar en archivo
            audit_logger.error(f"Error al registrar auditoría: {str(e)} | Acción original: {accion} - {descripcion}")
            return None

# Registro de Sesiones de Usuario
class SesionUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    perfil = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['usuario', 'activa']),
            models.Index(fields=['fecha_inicio']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}"

# Registro de Accesos Fallidos
class AccesoFallido(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    motivo = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Acceso fallido: {self.username} desde {self.ip_address} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

# Registro de Historial de Búsqueda
class HistorialBusqueda(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    perfil = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True)
    termino_busqueda = models.CharField(max_length=255, db_index=True)
    termino_normalizado = models.CharField(max_length=255, db_index=True, help_text="Término en minúsculas y sin espacios extra")
    resultados_encontrados = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['termino_normalizado', 'timestamp']),
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['termino_normalizado', '-timestamp']),
        ]
        verbose_name = "Historial de Búsqueda"
        verbose_name_plural = "Historial de Búsquedas"
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else 'Anónimo'
        return f"{usuario_str}: '{self.termino_busqueda}' ({self.resultados_encontrados} resultados) - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @classmethod
    def registrar_busqueda(cls, termino, usuario=None, perfil=None, resultados_count=0, ip_address='127.0.0.1', user_agent=''):
        """Método para registrar una nueva búsqueda"""
        if not termino or not termino.strip():
            return None
            
        termino_normalizado = termino.strip().lower()
        
        # Crear registro de búsqueda
        historial = cls.objects.create(
            usuario=usuario,
            perfil=perfil,
            termino_busqueda=termino.strip(),
            termino_normalizado=termino_normalizado,
            resultados_encontrados=resultados_count,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return historial
    
    @classmethod
    def obtener_mas_buscados(cls, limite=10, dias=30):
        """Obtener los términos más buscados en los últimos días"""
        from django.db.models import Count
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        return cls.objects.filter(
            timestamp__gte=fecha_limite
        ).values('termino_normalizado').annotate(
            total_busquedas=Count('id'),
            ultimo_termino_original=models.Max('termino_busqueda')
        ).order_by('-total_busquedas')[:limite]
    
    @classmethod
    def obtener_busquedas_usuario(cls, usuario, limite=20):
        """Obtener las búsquedas recientes de un usuario específico"""
        return cls.objects.filter(
            usuario=usuario
        ).order_by('-timestamp')[:limite]
    
    @classmethod
    def obtener_estadisticas_busqueda(cls, dias=7):
        """Obtener estadísticas de búsqueda para el periodo especificado"""
        from django.db.models import Count, Avg
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        stats = cls.objects.filter(timestamp__gte=fecha_limite).aggregate(
            total_busquedas=Count('id'),
            busquedas_unicas=Count('termino_normalizado', distinct=True),
            promedio_resultados=Avg('resultados_encontrados'),
            usuarios_unicos=Count('usuario', distinct=True)
        )
        
        return stats
