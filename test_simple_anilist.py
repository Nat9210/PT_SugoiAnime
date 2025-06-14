#!/usr/bin/env python
"""
Test simple de la API de AniList
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from myapp.anilist_api import anilist_api

def test_simple():
    """Prueba simple de la API original"""
    print("🧪 Probando API de AniList básica...")
    
    try:
        # Usar el método original que sabemos que funciona
        resultados = anilist_api.buscar_anime("Naruto", per_page=3)
        
        print(f"✅ Encontrados {len(resultados)} resultados:")
        
        for i, anime in enumerate(resultados, 1):
            title = anime.get('title', {})
            print(f"\n{i}. {title.get('romaji', 'N/A')}")
            print(f"   Inglés: {title.get('english', 'N/A')}")
            print(f"   Score: {anime.get('averageScore', 'N/A')}")
            print(f"   Popularidad: {anime.get('popularity', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
