from .models import Categoria

def base_context(request):
    # Lista de categorías en español
    categorias_espanol = [
        'Accion', 'Acción', 'Aventura', 'Ciencia Ficción', 'Comedia', 
        'Deportes', 'Drama', 'Fantasía', 'Musical', 'Recuentos de la vida', 
        'Romance', 'Sobrenatural', 'Thriller'
    ]
    
    categorias_menu = Categoria.objects.filter(
        nombre__in=categorias_espanol
    ).order_by('nombre')
    
    return {'categorias_menu': categorias_menu}