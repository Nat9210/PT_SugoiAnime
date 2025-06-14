from django.contrib import admin
from .models import (Contenido, Categoria, Episodio, ContenidoCategoria, Perfil, 
                     HistorialReproduccion, Favorito, Calificacion, AuditLog, 
                     SesionUsuario, AccesoFallido, HistorialBusqueda)
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Q
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

# Vista personalizada para estadísticas y recomendaciones
@staff_member_required
def estadisticas_recomendaciones(request):
    """Vista para mostrar estadísticas del sistema y recomendaciones"""
    
    # Estadísticas generales
    total_contenidos = Contenido.objects.count()
    total_usuarios = Perfil.objects.count()
    total_reproducciones = HistorialReproduccion.objects.count()
    total_calificaciones = Calificacion.objects.count()
    total_busquedas = HistorialBusqueda.objects.count()
    
    # Contenido más popular (por reproducciones)
    contenido_mas_visto = Contenido.objects.annotate(
        total_reproducciones=Count('historialreproduccion'),
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion')
    ).filter(
        total_reproducciones__gt=0
    ).order_by('-total_reproducciones')[:10]
    
    # Contenido mejor valorado
    contenido_mejor_valorado = Contenido.objects.annotate(
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion'),
        total_likes=Count('calificacion', filter=Q(calificacion__calificacion__gte=4))
    ).filter(
        total_calificaciones__gte=3
    ).order_by('-rating_promedio', '-total_calificaciones')[:10]
    
    # Contenido con más me gusta
    contenido_mas_gustado = Contenido.objects.annotate(
        total_likes=Count('calificacion', filter=Q(calificacion__calificacion__gte=4)),
        total_dislikes=Count('calificacion', filter=Q(calificacion__calificacion__lte=2)),
        rating_promedio=Avg('calificacion__calificacion')
    ).filter(
        total_likes__gt=0
    ).order_by('-total_likes', '-rating_promedio')[:10]
    
    # Términos más buscados
    terminos_mas_buscados = HistorialBusqueda.obtener_mas_buscados(limite=10, dias=30)
    
    # Categorías más populares
    categorias_populares = Categoria.objects.annotate(
        total_contenido=Count('contenidos'),
        total_reproducciones=Count('contenidos__historialreproduccion')
    ).filter(
        total_contenido__gt=0
    ).order_by('-total_reproducciones', '-total_contenido')[:10]
    
    context = {
        'title': 'Estadísticas y Recomendaciones',
        'estadisticas_generales': {
            'total_contenidos': total_contenidos,
            'total_usuarios': total_usuarios,
            'total_reproducciones': total_reproducciones,
            'total_calificaciones': total_calificaciones,
            'total_busquedas': total_busquedas,
        },
        'contenido_mas_visto': contenido_mas_visto,
        'contenido_mejor_valorado': contenido_mejor_valorado,
        'contenido_mas_gustado': contenido_mas_gustado,
        'terminos_mas_buscados': terminos_mas_buscados,
        'categorias_populares': categorias_populares,
    }
    
    return render(request, 'admin/estadisticas_recomendaciones.html', context)

# Personalizar el AdminSite para agregar la vista personalizada
class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        from .anilist_views import (
            anilist_dashboard, importar_populares_anilist, 
            importar_temporada_anilist, buscar_importar_anilist,
            buscar_anilist_ajax, importar_anime_especifico,
            buscar_e_importar_español_anilist
        )
        custom_urls = [
            path('estadisticas-recomendaciones/', estadisticas_recomendaciones, name='estadisticas_recomendaciones'),
            path('anilist/', anilist_dashboard, name='anilist_dashboard'),
            path('anilist/importar-populares/', importar_populares_anilist, name='importar_populares_anilist'),
            path('anilist/importar-temporada/', importar_temporada_anilist, name='importar_temporada_anilist'),
            path('anilist/buscar-importar/', buscar_importar_anilist, name='buscar_importar_anilist'),
            path('anilist/buscar-importar-español/', buscar_e_importar_español_anilist, name='buscar_e_importar_español_anilist'),
            path('anilist/buscar-ajax/', buscar_anilist_ajax, name='buscar_anilist_ajax'),
            path('anilist/importar-especifico/', importar_anime_especifico, name='importar_anime_especifico'),
        ]
        return custom_urls + urls

# Reemplazar el sitio de admin por defecto
admin_site = CustomAdminSite(name='custom_admin')

# Re-registrar todos los modelos en el sitio personalizado
admin_site.register(Contenido, ContenidoAdmin)
admin_site.register(Categoria)
admin_site.register(Episodio, EpisodioAdmin)
admin_site.register(ContenidoCategoria)
admin_site.register(Perfil)
admin_site.register(HistorialReproduccion)
admin_site.register(Favorito)
admin_site.register(Calificacion)
admin_site.register(AuditLog, AuditLogAdmin)
admin_site.register(SesionUsuario, SesionUsuarioAdmin)
admin_site.register(AccesoFallido, AccesoFallidoAdmin)
admin_site.register(HistorialBusqueda, HistorialBusquedaAdmin)

# Configurar títulos del sitio personalizado
admin_site.site_header = "SugoiAnime - Panel de Administración"
admin_site.site_title = "SugoiAnime Admin"
admin_site.index_title = "Panel de Control - Sistema de Auditoría Incluido"
