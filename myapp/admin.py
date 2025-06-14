from django.contrib import admin
from .models import (Contenido, Categoria, Episodio, ContenidoCategoria, Perfil, 
                     HistorialReproduccion, Favorito, Calificacion, AuditLog, 
                     SesionUsuario, AccesoFallido, HistorialBusqueda)
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

class ContenidoCategoriaInline(admin.TabularInline):
    model = ContenidoCategoria
    extra = 1

class EpisodioInline(admin.TabularInline):
    model = Episodio
    extra = 1
    fields = ('temporada', 'numero_episodio', 'titulo', 'duracion', 'video_url', 'video_file', 'descripcion')

class ContenidoAdmin(admin.ModelAdmin):
    inlines = [ContenidoCategoriaInline, EpisodioInline]
    list_display = ('titulo', 'tipo', 'año')
    search_fields = ('titulo',)
    list_filter = ('tipo', 'categorias')

class EpisodioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'serie', 'temporada', 'numero_episodio', 'duracion', 'has_video')
    list_filter = ('serie', 'temporada')
    search_fields = ('titulo', 'serie__titulo')
    
    def has_video(self, obj):
        return bool(obj.video_file) or bool(obj.video_url)
    has_video.short_description = "Tiene video"
    has_video.boolean = True

admin.site.register(Contenido, ContenidoAdmin)
admin.site.register(Categoria)
admin.site.register(Episodio, EpisodioAdmin)
admin.site.register(ContenidoCategoria)
admin.site.register(Perfil)
admin.site.register(HistorialReproduccion)
admin.site.register(Favorito)
admin.site.register(Calificacion)

# Administración de Auditoría y Logs
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'usuario', 'perfil', 'accion', 'nivel', 'descripcion_corta', 'ip_address')
    list_filter = ('accion', 'nivel', 'timestamp', 'tabla_afectada')
    search_fields = ('usuario__username', 'perfil__nombre', 'descripcion', 'ip_address')
    readonly_fields = ('timestamp', 'usuario', 'perfil', 'accion', 'tabla_afectada', 
                      'objeto_id', 'descripcion', 'nivel', 'ip_address', 'user_agent', 
                      'datos_adicionales_formatted')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:100] + '...' if len(obj.descripcion) > 100 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'
    
    def datos_adicionales_formatted(self, obj):
        if obj.datos_adicionales:
            return format_html('<pre>{}</pre>', json.dumps(obj.datos_adicionales, indent=2, ensure_ascii=False))
        return '-'
    datos_adicionales_formatted.short_description = 'Datos Adicionales'
    
    def has_add_permission(self, request):
        return False  # No permitir agregar registros manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Solo superusuarios pueden eliminar

@admin.register(SesionUsuario)
class SesionUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'perfil', 'fecha_inicio', 'fecha_fin', 'activa', 'duracion_sesion', 'ip_address')
    list_filter = ('activa', 'fecha_inicio', 'fecha_fin')
    search_fields = ('usuario__username', 'perfil__nombre', 'ip_address')
    readonly_fields = ('usuario', 'perfil', 'session_key', 'ip_address', 'user_agent', 
                      'fecha_inicio', 'fecha_fin', 'duracion_sesion')
    date_hierarchy = 'fecha_inicio'
    ordering = ('-fecha_inicio',)
    
    def duracion_sesion(self, obj):
        if obj.fecha_fin:
            duracion = obj.fecha_fin - obj.fecha_inicio
            total_seconds = int(duracion.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif obj.activa:
            return "Sesión activa"
        return "No finalizada"
    duracion_sesion.short_description = 'Duración'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(AccesoFallido)
class AccesoFallidoAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'timestamp', 'motivo')
    list_filter = ('timestamp', 'motivo')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('username', 'ip_address', 'user_agent', 'timestamp', 'motivo')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# Administración de Historial de Búsqueda
@admin.register(HistorialBusqueda)
class HistorialBusquedaAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'usuario', 'termino_busqueda', 'resultados_encontrados', 'ip_address')
    list_filter = ('timestamp', 'resultados_encontrados')
    search_fields = ('termino_busqueda', 'termino_normalizado', 'usuario__username')
    readonly_fields = ('timestamp', 'usuario', 'perfil', 'termino_busqueda', 'termino_normalizado', 
                      'resultados_encontrados', 'ip_address', 'user_agent')
    ordering = ('-timestamp',)
    list_per_page = 50
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# Personalizar el título del sitio de administración
admin.site.site_header = "SugoiAnime - Panel de Administración"
admin.site.site_title = "SugoiAnime Admin"
admin.site.index_title = "Panel de Control - Sistema de Auditoría Incluido"
