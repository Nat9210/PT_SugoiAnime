from django.contrib import admin
from .models import Contenido, Categoria, Episodio, ContenidoCategoria

class ContenidoCategoriaInline(admin.TabularInline):
    model = ContenidoCategoria
    extra = 1

class EpisodioInline(admin.TabularInline):
    model = Episodio
    extra = 1

class ContenidoAdmin(admin.ModelAdmin):
    inlines = [ContenidoCategoriaInline, EpisodioInline]

admin.site.register(Contenido, ContenidoAdmin)
admin.site.register(Categoria)
admin.site.register(Episodio)
admin.site.register(ContenidoCategoria)
