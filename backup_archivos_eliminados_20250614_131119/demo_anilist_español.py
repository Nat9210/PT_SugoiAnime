#!/usr/bin/env python
"""
Demostración de búsquedas específicas en español
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from myapp.anilist_api import anilist_api
from myapp.anilist_importer import anilist_importer

def demo_busquedas_español():
    """Demostrar búsquedas específicas en español"""
    print("🇪🇸 DEMOSTRACIÓN: Búsquedas de Anime en Español")
    print("=" * 60)
    
    # Búsquedas de ejemplo
    terminos_demo = [
        "Attack on Titan",  # Término en inglés (debería encontrar versiones españolas)
        "Dragon Ball",      # Término universal
        "Studio Ghibli",    # Estudio popular
    ]
    
    for termino in terminos_demo:
        print(f"\n🔍 Buscando: '{termino}'")
        print("-" * 40)
        
        try:
            # Usar búsqueda especializada en español
            resultados = anilist_api.buscar_anime_español(termino, per_page=3)
            
            if resultados:
                for i, anime in enumerate(resultados, 1):
                    title = anime.get('title', {})
                    synonyms = anime.get('synonyms', [])
                    
                    # Obtener título preferido usando nuestro algoritmo
                    titulo_preferido = anilist_importer._obtener_titulo_preferido(title, synonyms)
                    es_español = anilist_importer._es_titulo_español(titulo_preferido)
                    
                    print(f"\n{i}. {titulo_preferido}")
                    print(f"   🏷️  Romaji: {title.get('romaji', 'N/A')}")
                    print(f"   🌐 Inglés: {title.get('english', 'N/A')}")
                    print(f"   📝 Sinónimos: {', '.join(synonyms[:2]) if synonyms else 'N/A'}")
                    print(f"   🇪🇸 ¿En español?: {'✅ SÍ' if es_español else '❌ NO'}")
                    print(f"   ⭐ Score: {anime.get('averageScore', 'N/A')}")
                    print(f"   👥 Popularidad: {anime.get('popularity', 'N/A'):,}")
                    
                    # Mostrar géneros
                    genres = anime.get('genres', [])
                    if genres:
                        print(f"   🎭 Géneros: {', '.join(genres[:3])}")
            else:
                print("   ❌ No se encontraron resultados")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n\n📊 RESUMEN DE CONTENIDO ACTUAL:")
    print("=" * 60)
    
    from myapp.models import Contenido
    
    # Estadísticas
    total = Contenido.objects.count()
    anilist = Contenido.objects.filter(anilist_id__isnull=False).count()
    
    print(f"📈 Total de contenidos: {total}")
    print(f"🎌 Importados de AniList: {anilist}")
    print(f"🏠 Contenidos locales: {total - anilist}")
    
    # Contenidos mejor valorados de AniList
    print(f"\n🏆 TOP 5 MEJOR VALORADOS (AniList):")
    top_rated = Contenido.objects.filter(
        anilist_score__isnull=False
    ).order_by('-anilist_score')[:5]
    
    for i, contenido in enumerate(top_rated, 1):
        print(f"{i}. {contenido.titulo} - {contenido.anilist_score}⭐")
    
    # Contenidos populares de AniList
    print(f"\n🔥 TOP 5 MÁS POPULARES (AniList):")
    top_popular = Contenido.objects.filter(
        anilist_popularity__isnull=False
    ).order_by('-anilist_popularity')[:5]
    
    for i, contenido in enumerate(top_popular, 1):
        popularity = f"{contenido.anilist_popularity:,}" if contenido.anilist_popularity else "N/A"
        print(f"{i}. {contenido.titulo} - {popularity} usuarios")
    
    print(f"\n✅ El sistema de importación de AniList con énfasis en español está funcionando perfectamente!")

if __name__ == "__main__":
    demo_busquedas_español()
