from .models import Categoria

def base_context(request):
    categorias_menu = Categoria.objects.all().order_by('nombre')
    return {'categorias_menu': categorias_menu}