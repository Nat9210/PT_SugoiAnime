#!/usr/bin/env python
"""
Script para validar que el index muestre contenido dinámico correctamente
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from myapp.models import Contenido
from django.db.models import Count, Avg, Q

def validar_contenido_dinamico():
    """Validar que hay suficiente contenido para las secciones dinámicas"""
    print("📊 Validando contenido dinámico para el index...")
    
    # 1. Contenido destacado para hero slider
    contenido_destacado = Contenido.objects.annotate(
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion'),
        total_reproducciones=Count('historialreproduccion')
    ).filter(
        imagen_portada__isnull=False
    ).order_by('-rating_promedio', '-total_reproducciones')[:4]
    
    print(f"\n🎬 Contenido destacado para hero slider: {len(contenido_destacado)} elementos")
    for i, contenido in enumerate(contenido_destacado, 1):
        print(f"  {i}. {contenido.titulo}")
        print(f"     - Imagen: {'✅' if contenido.imagen_portada else '❌'}")
        print(f"     - Rating: {contenido.rating_promedio:.1f if contenido.rating_promedio else 'N/A'}")
        print(f"     - Reproducciones: {contenido.total_reproducciones}")
        print(f"     - Categorías: {', '.join([c.nombre for c in contenido.categorias.all()[:3]])}")
    
    # 2. Contenido más gustado (con más likes)
    contenido_mas_gustado = Contenido.objects.annotate(
        total_likes=Count('calificacion', filter=Q(calificacion__calificacion__gte=4)),
        rating_promedio=Avg('calificacion__calificacion')
    ).filter(
        total_likes__gt=0
    ).order_by('-total_likes', '-rating_promedio')[:6]
    
    print(f"\n❤️ Contenido con más me gusta: {len(contenido_mas_gustado)} elementos")
    for i, contenido in enumerate(contenido_mas_gustado, 1):
        print(f"  {i}. {contenido.titulo}")
        print(f"     - Likes: {contenido.total_likes}")
        print(f"     - Rating: {contenido.rating_promedio:.1f if contenido.rating_promedio else 'N/A'}")
        print(f"     - Imagen: {'✅' if contenido.imagen_portada else '❌'}")
    
    # 3. Contenido mejor valorado
    contenido_mejor_valorado = Contenido.objects.annotate(
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion')
    ).filter(
        total_calificaciones__gte=1
    ).order_by('-rating_promedio', '-total_calificaciones')[:6]
    
    print(f"\n⭐ Contenido mejor valorado: {len(contenido_mejor_valorado)} elementos")
    for i, contenido in enumerate(contenido_mejor_valorado, 1):
        print(f"  {i}. {contenido.titulo}")
        print(f"     - Rating: {contenido.rating_promedio:.1f if contenido.rating_promedio else 'N/A'}")
        print(f"     - Total calificaciones: {contenido.total_calificaciones}")
        print(f"     - Imagen: {'✅' if contenido.imagen_portada else '❌'}")
    
    # 4. Contenido más buscado
    from myapp.models import HistorialBusqueda
    terminos_mas_buscados = HistorialBusqueda.obtener_mas_buscados(limite=8, dias=30)
    
    print(f"\n🔍 Términos más buscados: {len(terminos_mas_buscados)} elementos")
    for i, termino_data in enumerate(terminos_mas_buscados, 1):
        print(f"  {i}. '{termino_data['termino_normalizado']}' - {termino_data['total_busquedas']} búsquedas")
    
    # Contenido relacionado con búsquedas
    contenido_mas_buscado = []
    if terminos_mas_buscados:
        for termino_data in terminos_mas_buscados[:6]:
            termino = termino_data['termino_normalizado']
            contenidos_relacionados = Contenido.objects.filter(
                Q(titulo__icontains=termino) | 
                Q(descripcion__icontains=termino) | 
                Q(categorias__nombre__icontains=termino)
            ).distinct()[:3]
            for contenido in contenidos_relacionados:
                if contenido not in contenido_mas_buscado:
                    contenido_mas_buscado.append(contenido)
                if len(contenido_mas_buscado) >= 8:
                    break
            if len(contenido_mas_buscado) >= 8:
                break
    
    print(f"\n🔥 Contenido relacionado con búsquedas: {len(contenido_mas_buscado)} elementos")
    for i, contenido in enumerate(contenido_mas_buscado, 1):
        print(f"  {i}. {contenido.titulo}")
        print(f"     - Imagen: {'✅' if contenido.imagen_portada else '❌'}")
    
    # 5. Estadísticas generales
    total_contenido = Contenido.objects.count()
    contenido_con_imagen = Contenido.objects.filter(imagen_portada__isnull=False).count()
    contenido_con_rating = Contenido.objects.annotate(
        total_calificaciones=Count('calificacion')
    ).filter(total_calificaciones__gt=0).count()
    
    print(f"\n📈 Estadísticas generales:")
    print(f"  - Total contenido: {total_contenido}")
    print(f"  - Con imagen de portada: {contenido_con_imagen} ({contenido_con_imagen/total_contenido*100:.1f}%)")
    print(f"  - Con calificaciones: {contenido_con_rating} ({contenido_con_rating/total_contenido*100:.1f}%)")
    
    # Verificar problemas
    problemas = []
    if len(contenido_destacado) < 4:
        problemas.append(f"⚠️ Solo {len(contenido_destacado)}/4 elementos para hero slider")
    if len(contenido_mas_gustado) == 0:
        problemas.append("⚠️ No hay contenido con likes para mostrar")
    if len(contenido_mejor_valorado) == 0:
        problemas.append("⚠️ No hay contenido valorado para mostrar")
    if contenido_con_imagen < total_contenido * 0.5:
        problemas.append("⚠️ Menos del 50% del contenido tiene imagen de portada")
    
    if problemas:
        print(f"\n❌ Problemas detectados:")
        for problema in problemas:
            print(f"  {problema}")
    else:
        print(f"\n✅ Todas las secciones tienen contenido suficiente!")
    
    return len(problemas) == 0

if __name__ == "__main__":
    print("🎌 Validación de Contenido Dinámico - Index")
    print("=" * 50)
    
    try:
        exito = validar_contenido_dinamico()
        
        if exito:
            print("\n🎉 ¡El index está listo con contenido dinámico!")
        else:
            print("\n⚠️ Hay algunos problemas que podrían afectar la visualización.")
            
    except Exception as e:
        print(f"\n❌ Error durante la validación: {e}")
        import traceback
        traceback.print_exc()
