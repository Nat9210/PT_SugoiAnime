from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from .models import (Contenido, Categoria, Episodio, ContenidoCategoria, Perfil, 
                     HistorialReproduccion, Favorito, Calificacion, AuditLog)
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
    list_display = ('titulo', 'tipo', 'año', 'imagen_preview', 'total_episodios', 'popularidad_score', 'tiene_video')
    search_fields = ('titulo', 'descripcion')
    list_filter = ('tipo', 'categorias', 'año', 'idioma')
    list_per_page = 25
    readonly_fields = ('imagen_preview_large', 'fecha_importacion', 'estadisticas_content')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'tipo', 'año', 'idioma', 'descripcion')
        }),
        ('Multimedia', {
            'fields': ('imagen_portada', 'imagen_preview_large', 'video_url'),
            'classes': ('collapse',)
        }),
        ('Datos Técnicos', {
            'fields': ('duracion', 'anilist_id', 'anilist_url', 'anilist_score', 'anilist_popularity'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('estadisticas_content',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_importacion',),
            'classes': ('collapse',)
        }),
    )
    
    def imagen_preview(self, obj):
        if obj.imagen_portada:
            return format_html(
                '<img src="{}" style="width: 50px; height: 70px; object-fit: cover; border-radius: 5px;" />',
                obj.imagen_portada.url
            )
        return "Sin imagen"
    imagen_preview.short_description = "Portada"
    
    def imagen_preview_large(self, obj):
        if obj.imagen_portada:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 300px; object-fit: cover; border-radius: 10px;" />',
                obj.imagen_portada.url
            )
        return "Sin imagen disponible"
    imagen_preview_large.short_description = "Vista previa de portada"
    
    def total_episodios(self, obj):
        count = obj.episodio_set.count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', count)
        return format_html('<span style="color: orange;">0</span>')
    total_episodios.short_description = "Episodios"
    
    def popularidad_score(self, obj):
        score = getattr(obj, 'anilist_popularity', 0) or 0
        if score > 50000:
            color = "green"
        elif score > 10000:
            color = "orange"
        else:
            color = "gray"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, score)
    popularidad_score.short_description = "Popularidad"
    
    def tiene_video(self, obj):
        has_video = obj.video_url or obj.episodio_set.filter(
            Q(video_url__isnull=False) | Q(video_file__isnull=False)
        ).exists()
        if has_video:
            return format_html('<span style="color: green;">✓ Sí</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    tiene_video.short_description = "Tiene Video"
    # tiene_video.boolean = True  # Comentado para permitir HTML personalizado
    
    def estadisticas_content(self, obj):
        try:
            reproducciones = obj.historialreproduccion_set.count()
            calificaciones = obj.calificacion_set.count()
            favoritos = obj.favorito_set.count()
            rating = obj.calificacion_set.aggregate(promedio=Avg('calificacion'))['promedio']
            
            return format_html(
                '''
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; line-height: 1.6;">
                    <strong>📊 Estadísticas de Contenido:</strong><br>
                    🔥 Reproducciones: <strong style="color: #007cba;">{}</strong><br>
                    ⭐ Calificaciones: <strong style="color: #007cba;">{}</strong><br>
                    ❤️ Favoritos: <strong style="color: #007cba;">{}</strong><br>
                    📈 Rating promedio: <strong style="color: #007cba;">{}</strong>
                </div>
                ''',
                reproducciones,
                calificaciones, 
                favoritos,
                f"{rating:.1f}" if rating else "Sin calificar"
            )
        except:
            return "Estadísticas no disponibles"
    estadisticas_content.short_description = "Estadísticas de uso"
    
class EpisodioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'serie', 'temporada', 'numero_episodio', 'duracion', 'video_status', 'reproductions_count')
    list_filter = ('serie', 'temporada', 'serie__tipo')
    search_fields = ('titulo', 'serie__titulo', 'descripcion')
    list_per_page = 50
    autocomplete_fields = ['serie']
    
    fieldsets = (
        ('Información del Episodio', {
            'fields': ('serie', 'temporada', 'numero_episodio', 'titulo', 'descripcion')
        }),
        ('Contenido', {
            'fields': ('duracion', 'video_url', 'video_file'),
        }),
        ('Estadísticas', {
            'fields': ('episode_stats',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('episode_stats',)
    
    def video_status(self, obj):
        if obj.video_file:
            return format_html('<span style="color: green; font-weight: bold;">📁 Archivo Local</span>')
        elif obj.video_url:
            return format_html('<span style="color: blue; font-weight: bold;">🔗 URL Externa</span>')
        else:
            return format_html('<span style="color: red;">❌ Sin Video</span>')
    video_status.short_description = "Estado del Video"
    
    def reproductions_count(self, obj):
        count = obj.historialreproduccion_set.count()
        if count > 100:
            color = "green"
        elif count > 10:
            color = "orange"
        else:
            color = "gray"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, count)
    reproductions_count.short_description = "Reproducciones"
    
    def episode_stats(self, obj):
        try:
            reproducciones = obj.historialreproduccion_set.count()
            usuarios_unicos = obj.historialreproduccion_set.values('perfil').distinct().count()
            
            return format_html(
                '''
                <div style="background: #f0f8ff; padding: 15px; border-radius: 8px; border-left: 4px solid #007cba;">
                    <strong>📺 Estadísticas del Episodio:</strong><br>
                    👁️ Total reproducciones: <strong>{}</strong><br>
                    👥 Usuarios únicos: <strong>{}</strong><br>
                    📊 Promedio por usuario: <strong>{:.1f}</strong>
                </div>
                ''',
                reproducciones,
                usuarios_unicos,
                reproducciones / usuarios_unicos if usuarios_unicos > 0 else 0
            )
        except:
            return "Estadísticas no disponibles"
    episode_stats.short_description = "Estadísticas detalladas"

admin.site.register(Contenido, ContenidoAdmin)
admin.site.register(Categoria)
admin.site.register(Episodio, EpisodioAdmin)
admin.site.register(ContenidoCategoria)
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario', 'avatar_preview', 'tipo', 'actividad_stats', 'favoritos_count')
    search_fields = ('nombre', 'usuario__username', 'usuario__email')
    list_filter = ('tipo', 'usuario__is_active')
    readonly_fields = ('avatar_preview_large', 'user_activity_summary', 'recommendations_summary')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'nombre', 'avatar', 'avatar_preview_large')
        }),
        ('Actividad del Usuario', {
            'fields': ('user_activity_summary',),
            'classes': ('collapse',)
        }),
        ('Sistema de Recomendaciones', {
            'fields': ('recommendations_summary',),
            'classes': ('collapse',)
        }),
    )
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "👤"
    avatar_preview.short_description = "Avatar"
    
    def avatar_preview_large(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 150px; height: 150px; border-radius: 50%; object-fit: cover; border: 3px solid #ddd;" />',
                obj.avatar.url
            )
        return "No hay avatar configurado"
    avatar_preview_large.short_description = "Avatar del usuario"
    
    def actividad_stats(self, obj):
        reproducciones = obj.historialreproduccion_set.count()
        calificaciones = obj.calificacion_set.count()
        
        if reproducciones > 100:
            badge = "🔥 Usuario Activo"
            color = "green"
        elif reproducciones > 20:
            badge = "📺 Usuario Regular" 
            color = "orange"
        else:
            badge = "👤 Usuario Nuevo"
            color = "gray"
            
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, badge)
    actividad_stats.short_description = "Nivel de Actividad"
    
    def favoritos_count(self, obj):
        count = obj.favorito_set.count()
        return format_html('<span style="color: red;">❤️ {}</span>', count)
    favoritos_count.short_description = "Favoritos"
    
    def user_activity_summary(self, obj):
        try:
            reproducciones = obj.historialreproduccion_set.count()
            calificaciones = obj.calificacion_set.count()
            favoritos = obj.favorito_set.count()
            # busquedas = obj.historialbusqueda_set.count()  # Modelo eliminado
            
            # Contenido más visto
            top_content = obj.historialreproduccion_set.values('contenido__titulo').annotate(
                count=Count('contenido')
            ).order_by('-count')[:3]
            
            top_content_html = ""
            for item in top_content:
                top_content_html += f"• {item['contenido__titulo']} ({item['count']} veces)<br>"
            
            return format_html(
                '''
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; line-height: 1.8;">
                    <h3 style="color: #333; margin-top: 0;">📊 Resumen de Actividad</h3>
                    
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 15px 0;">
                        <div>
                            <strong>📺 Reproducciones:</strong> {}<br>
                            <strong>⭐ Calificaciones:</strong> {}<br>
                        </div>
                        <div>
                            <strong>❤️ Favoritos:</strong> {}<br>
                            <strong>🔍 Búsquedas:</strong> {}<br>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px;">
                        <strong> Contenido más visto:</strong><br>
                        <div style="margin-left: 10px; color: #666;">
                            {}
                        </div>
                    </div>
                </div>
                ''',
                reproducciones, calificaciones, favoritos, 0,  # busquedas reemplazado por 0
                top_content_html if top_content_html else "No hay actividad registrada"
            )
        except:
            return "Resumen no disponible"
    user_activity_summary.short_description = "Actividad completa del usuario"
    
    def recommendations_summary(self, obj):
        try:
            from .recommendations import obtener_recomendaciones_para_perfil
            recomendaciones = obtener_recomendaciones_para_perfil(obj, limite=5)
            
            if recomendaciones:
                rec_html = ""
                for rec in recomendaciones:
                    rec_html += f"• {rec.titulo}<br>"
                
                return format_html(
                    '''
                    <div style="background: #e8f4fd; padding: 15px; border-radius: 8px; border-left: 4px solid #007cba;">
                        <strong> Recomendaciones Actuales:</strong><br>
                        <div style="margin-left: 10px; margin-top: 10px; color: #333;">
                            {}
                        </div>
                    </div>
                    ''',
                    rec_html
                )
            else:
                return format_html(
                    '<div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #856404;">'
                    'No hay recomendaciones disponibles. El usuario necesita más actividad.'
                    '</div>'
                )
        except:
            return "Sistema de recomendaciones no disponible"
    recommendations_summary.short_description = "Estado del sistema de recomendaciones"
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
    # total_busquedas = HistorialBusqueda.objects.count()  # Modelo eliminado
    
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
    # terminos_mas_buscados = HistorialBusqueda.obtener_mas_buscados(limite=10, dias=30)  # Modelo eliminado
    
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
            # 'total_busquedas': total_busquedas,  # Modelo eliminado
        },
        'contenido_mas_visto': contenido_mas_visto,
        'contenido_mejor_valorado': contenido_mejor_valorado,
        'contenido_mas_gustado': contenido_mas_gustado,
        # 'terminos_mas_buscados': terminos_mas_buscados,  # Modelo eliminado
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
    
    def index(self, request, extra_context=None):
        """
        Personalizar la página principal del admin con métricas
        """
        # Métricas básicas para el dashboard
        try:
            total_contenidos = Contenido.objects.count()
            total_usuarios = Perfil.objects.count()
            total_reproducciones = HistorialReproduccion.objects.count()
            total_calificaciones = Calificacion.objects.count()
            total_busquedas = 0  # Modelo eliminado, valor por defecto
        except:
            # En caso de error (ej: base de datos no inicializada)
            total_contenidos = 0
            total_usuarios = 0
            total_reproducciones = 0
            total_calificaciones = 0
            total_busquedas = 0
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_contenidos': total_contenidos,
            'total_usuarios': total_usuarios,
            'total_reproducciones': total_reproducciones,
            'total_calificaciones': total_calificaciones,
            'total_busquedas': total_busquedas,
        })
        
        return super().index(request, extra_context)

# Reemplazar el sitio de admin por defecto
admin_site = CustomAdminSite(name='custom_admin')

# Re-registrar todos los modelos en el sitio personalizado
admin_site.register(Contenido, ContenidoAdmin)
admin_site.register(Categoria)
admin_site.register(Episodio, EpisodioAdmin)
admin_site.register(ContenidoCategoria)
admin_site.register(Perfil, PerfilAdmin)
admin_site.register(HistorialReproduccion)
admin_site.register(Favorito)
admin_site.register(Calificacion)
admin_site.register(AuditLog, AuditLogAdmin)

# Configurar títulos del sitio personalizado
admin_site.site_header = "SugoiAnime - Panel de Administración"
admin_site.site_title = "SugoiAnime Admin"
admin_site.index_title = "Panel de Control - Sistema de Auditoría Incluido"

# Registro de modelos de Django auth
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'groups')
    ordering = ('username',)
    readonly_fields = ('last_login',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email', 'avatar')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    def has_add_permission(self, request):
        return False  # No permitir agregar usuarios manualmente
    
    def has_change_permission(self, request, obj=None):
        return True  # Permitir editar usuarios

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class GroupAdmin(BaseGroupAdmin):
    list_display = ('name', 'permissions_list')
    search_fields = ('name',)
    
    def permissions_list(self, obj):
        return ", ".join([perm.codename for perm in obj.permissions.all()])
    permissions_list.short_description = 'Permisos'
    
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

# ===== CONFIGURACIÓN DEL SITIO PERSONALIZADO =====

# Definir clases admin para User y Group en el sitio personalizado
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

class CustomGroupAdmin(BaseGroupAdmin):
    list_display = ('name', 'permissions_count')
    search_fields = ('name',)
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = 'Cantidad de Permisos'

# Registrar User y Group en el sitio personalizado
admin_site.register(User, CustomUserAdmin)
admin_site.register(Group, CustomGroupAdmin)