#!/usr/bin/env python
"""
Script para probar la funcionalidad de importación de AniList con énfasis en español
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

def test_busqueda_español():
    """Probar búsqueda específica en español"""
    print("🇪🇸 Probando búsqueda especializada en español...")
    
    # Términos de prueba en español
    terminos_prueba = [
        "El Ataque de los Titanes",
        "One Piece en español",
        "Naruto español",
        "Dragon Ball",
        "Los Caballeros del Zodíaco"
    ]
    
    for termino in terminos_prueba:
        print(f"\n--- Buscando: {termino} ---")
        
        try:
            # Buscar usando el método especializado
            resultados = anilist_api.buscar_anime_español(termino, per_page=5)
            
            print(f"Encontrados {len(resultados)} resultados:")
            
            for i, anime in enumerate(resultados[:3], 1):
                title = anime.get('title', {})
                synonyms = anime.get('synonyms', [])
                description = anime.get('description', '')[:100] + "..." if anime.get('description') else ""
                
                print(f"\n{i}. ID: {anime.get('id')}")
                print(f"   Título Romaji: {title.get('romaji', 'N/A')}")
                print(f"   Título Inglés: {title.get('english', 'N/A')}")
                print(f"   Título Nativo: {title.get('native', 'N/A')}")
                print(f"   Sinónimos: {synonyms[:3] if synonyms else 'N/A'}")
                print(f"   Descripción: {description}")
                print(f"   Popularidad: {anime.get('popularity', 'N/A')}")
                print(f"   Score: {anime.get('averageScore', 'N/A')}")
                
                # Verificar indicadores de español
                titulo_preferido = anilist_importer._obtener_titulo_preferido(title, synonyms)
                es_español = anilist_importer._es_titulo_español(titulo_preferido)
                print(f"   Título preferido: {titulo_preferido}")
                print(f"   ¿Contiene español?: {es_español}")
                
        except Exception as e:
            print(f"Error al buscar '{termino}': {e}")

def test_importacion_español():
    """Probar importación con énfasis en español"""
    print("\n\n🚀 Probando importación de contenido en español...")
    
    termino_test = "Naruto"
    
    try:
        print(f"Importando contenido relacionado con: {termino_test}")
        contenidos = anilist_importer.buscar_e_importar_español(termino_test, max_resultados=3)
        
        print(f"\n✅ Importados {len(contenidos)} contenidos:")
        
        for contenido in contenidos:
            print(f"\n- {contenido.titulo}")
            print(f"  Tipo: {contenido.tipo}")
            print(f"  Año: {contenido.año}")
            print(f"  AniList ID: {contenido.anilist_id}")
            print(f"  Score AniList: {contenido.anilist_score}")
            print(f"  Popularidad: {contenido.anilist_popularity}")
            print(f"  Descripción: {contenido.descripcion[:100]}...")
            
    except Exception as e:
        print(f"Error en importación: {e}")

def test_detección_español():
    """Probar detección de títulos en español"""
    print("\n\n🔍 Probando detección de títulos en español...")
    
    titulos_prueba = [
        "El Ataque de los Titanes",
        "Los Caballeros del Zodíaco",
        "Attack on Titan",
        "Shingeki no Kyojin",
        "Naruto: Shippuden",
        "Dragon Ball Z en Español",
        "One Piece (Latino)",
        "進撃の巨人",
        "La Torre de Dios",
        "El Rey Demonio",
        "Kimetsu no Yaiba"
    ]
    
    for titulo in titulos_prueba:
        es_español = anilist_importer._es_titulo_español(titulo)
        estado = "✅ SÍ" if es_español else "❌ NO"
        print(f"{estado} - '{titulo}'")

if __name__ == "__main__":
    print("🎌 Test de Funcionalidad AniList en Español 🇪🇸")
    print("=" * 50)
    
    try:
        # Test 1: Detección de español
        test_detección_español()
        
        # Test 2: Búsqueda especializada
        test_busqueda_español()
        
        # Test 3: Importación (comentado por defecto para evitar spam en BD)
        respuesta = input("\n¿Desea probar la importación real? (puede crear registros en la BD) [y/N]: ")
        if respuesta.lower() in ['y', 'yes', 'sí', 's']:
            test_importacion_español()
        else:
            print("Importación saltada.")
        
        print("\n🎉 Pruebas completadas!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
