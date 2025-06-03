from django.contrib import admin
# Temporalmente comentado para resolver error de importación
# from .models import Contenido, Categoria, Episodio, ContenidoCategoria, Perfil, HistorialReproduccion, Favorito, Comentario

from django.contrib import admin
from .models import Contenido, Categoria, Episodio, ContenidoCategoria, Perfil, HistorialReproduccion, Favorito, Comentario

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
admin.site.register(Comentario)
