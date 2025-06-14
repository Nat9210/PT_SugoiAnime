"""
Vistas para la integración con AniList
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .anilist_importer import anilist_importer
from .anilist_api import anilist_api
from .models import Contenido
import json

@staff_member_required
def anilist_dashboard(request):
    """Dashboard principal para la integración con AniList"""
    total_contenidos = Contenido.objects.count()
    contenidos_anilist = Contenido.objects.filter(anilist_id__isnull=False).count()
    contenidos_locales = total_contenidos - contenidos_anilist
    
    context = {
        'title': 'Integración AniList',
        'total_contenidos': total_contenidos,
        'contenidos_anilist': contenidos_anilist,
        'contenidos_locales': contenidos_locales,
    }
    return render(request, 'admin/anilist_dashboard.html', context)

@staff_member_required
def importar_populares_anilist(request):
    """Importar anime populares desde AniList"""
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 20))
            if cantidad > 50:
                cantidad = 50  # Limitar para evitar sobrecarga
            
            contenidos = anilist_importer.importar_populares(cantidad)
            
            messages.success(
                request, 
                f'Se importaron {len(contenidos)} animes populares desde AniList.'
            )
            
        except Exception as e:
            messages.error(request, f'Error al importar: {str(e)}')
    
    return redirect('custom_admin:anilist_dashboard')

@staff_member_required
def importar_temporada_anilist(request):
    """Importar anime de la temporada actual desde AniList"""
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 20))
            if cantidad > 50:
                cantidad = 50
            
            contenidos = anilist_importer.importar_temporada_actual(cantidad)
            
            messages.success(
                request, 
                f'Se importaron {len(contenidos)} animes de la temporada actual desde AniList.'
            )
            
        except Exception as e:
            messages.error(request, f'Error al importar: {str(e)}')
    
    return redirect('custom_admin:anilist_dashboard')

@staff_member_required
def buscar_importar_anilist(request):
    """Buscar e importar anime específico desde AniList"""
    if request.method == 'POST':
        try:
            termino = request.POST.get('termino', '').strip()
            cantidad = int(request.POST.get('cantidad', 10))
            
            if not termino:
                messages.error(request, 'Debe especificar un término de búsqueda.')
                return redirect('custom_admin:anilist_dashboard')
            
            if cantidad > 20:
                cantidad = 20
            
            contenidos = anilist_importer.buscar_e_importar(termino, cantidad)
            
            if contenidos:
                messages.success(
                    request, 
                    f'Se importaron {len(contenidos)} animes buscando "{termino}" desde AniList.'
                )
            else:
                messages.warning(
                    request, 
                    f'No se encontraron resultados para "{termino}" en AniList.'
                )
            
        except Exception as e:
            messages.error(request, f'Error en la búsqueda: {str(e)}')
    
    return redirect('custom_admin:anilist_dashboard')

@staff_member_required
@csrf_exempt
def buscar_anilist_ajax(request):
    """Búsqueda AJAX en AniList para vista previa"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            termino = data.get('termino', '').strip()
            
            if not termino:
                return JsonResponse({'error': 'Término de búsqueda requerido'}, status=400)
            
            # Buscar en AniList
            resultados = anilist_api.buscar_anime(termino, per_page=10)
            
            # Formatear resultados para la respuesta
            anime_list = []
            for anime in resultados:
                title = anime.get('title', {})
                cover = anime.get('coverImage', {})
                
                anime_info = {
                    'id': anime.get('id'),
                    'titulo': (title.get('english') or 
                              title.get('romaji') or 
                              title.get('native', 'Sin título')),
                    'descripcion': anime.get('description', '')[:200] + '...' if anime.get('description') else '',
                    'año': anime.get('startDate', {}).get('year'),
                    'episodios': anime.get('episodes'),
                    'score': anime.get('averageScore'),
                    'popularidad': anime.get('popularity'),
                    'generos': anime.get('genres', []),
                    'imagen': cover.get('medium') or cover.get('large'),
                    'formato': anime.get('format'),
                    'estado': anime.get('status'),
                    'ya_importado': Contenido.objects.filter(anilist_id=anime.get('id')).exists()
                }
                anime_list.append(anime_info)
            
            return JsonResponse({
                'success': True,
                'resultados': anime_list
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@staff_member_required
@csrf_exempt
def importar_anime_especifico(request):
    """Importar un anime específico por ID de AniList"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            anilist_id = data.get('anilist_id')
            
            if not anilist_id:
                return JsonResponse({'error': 'ID de AniList requerido'}, status=400)
            
            # Verificar si ya existe
            if Contenido.objects.filter(anilist_id=anilist_id).exists():
                return JsonResponse({'error': 'Este anime ya ha sido importado'}, status=400)
            
            # Obtener datos detallados del anime
            anime_data = anilist_api.obtener_anime_por_id(anilist_id)
            
            if not anime_data:
                return JsonResponse({'error': 'No se pudo obtener información del anime'}, status=404)
            
            # Importar el anime
            contenido = anilist_importer.importar_anime_desde_anilist(anime_data)
            
            if contenido:
                return JsonResponse({
                    'success': True,
                    'mensaje': f'Anime "{contenido.titulo}" importado exitosamente',
                    'contenido_id': contenido.id
                })
            else:
                return JsonResponse({'error': 'Error al importar el anime'}, status=500)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@staff_member_required
def buscar_e_importar_español_anilist(request):
    """Buscar e importar anime con énfasis en contenido en español desde AniList"""
    if request.method == 'POST':
        try:
            termino = request.POST.get('termino', '').strip()
            cantidad = int(request.POST.get('cantidad', 10))
            
            if not termino:
                messages.error(request, 'Debe proporcionar un término de búsqueda.')
                return redirect('custom_admin:anilist_dashboard')
            
            if cantidad > 20:
                cantidad = 20  # Limitar para evitar sobrecarga
            
            contenidos = anilist_importer.buscar_e_importar_español(termino, cantidad)
            
            if contenidos:
                messages.success(
                    request, 
                    f'Se importaron {len(contenidos)} animes con énfasis en español buscando "{termino}" desde AniList.'
                )
            else:
                messages.warning(
                    request, 
                    f'No se encontraron resultados para "{termino}" en AniList con énfasis en español.'
                )
            
        except Exception as e:
            messages.error(request, f'Error en la búsqueda en español: {str(e)}')
    
    return redirect('custom_admin:anilist_dashboard')
