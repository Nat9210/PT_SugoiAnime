# Script para probar la integración con AniList
# Ejecutar: python manage.py shell < test_anilist.py

print("🌐 Probando integración con AniList...")

from myapp.anilist_api import anilist_api
from myapp.anilist_importer import anilist_importer
from myapp.models import Contenido

# Test 1: Probar conexión con AniList
print("\n1. Probando conexión con AniList...")
try:
    resultados = anilist_api.buscar_anime("Naruto", per_page=3)
    if resultados:
        print(f"✅ Conexión exitosa. Encontrados {len(resultados)} resultados para 'Naruto'")
        for i, anime in enumerate(resultados, 1):
            title = anime.get('title', {})
            titulo = title.get('english') or title.get('romaji') or 'Sin título'
            año = anime.get('startDate', {}).get('year', 'N/A')
            score = anime.get('averageScore', 'N/A')
            print(f"  {i}. {titulo} ({año}) - Score: {score}")
    else:
        print("❌ No se pudieron obtener resultados")
except Exception as e:
    print(f"❌ Error de conexión: {e}")

# Test 2: Probar importación de contenido
print("\n2. Probando importación de contenido...")
try:
    # Buscar anime de prueba
    anime_prueba = anilist_api.buscar_anime("Your Name", per_page=1)
    if anime_prueba:
        anime_data = anime_prueba[0]
        print(f"📥 Intentando importar: {anime_data.get('title', {}).get('romaji', 'N/A')}")
        
        # Verificar si ya existe
        anilist_id = anime_data.get('id')
        if Contenido.objects.filter(anilist_id=anilist_id).exists():
            print("ℹ️  Este anime ya está importado")
        else:
            # Importar
            contenido = anilist_importer.importar_anime_desde_anilist(anime_data)
            if contenido:
                print(f"✅ Anime importado exitosamente: {contenido.titulo}")
                print(f"   - Tipo: {contenido.tipo}")
                print(f"   - Año: {contenido.año}")
                print(f"   - Duración: {contenido.duracion} min")
                print(f"   - Categorías: {contenido.categorias.count()}")
                print(f"   - AniList ID: {contenido.anilist_id}")
                print(f"   - AniList Score: {contenido.anilist_score}")
            else:
                print("❌ Error al importar anime")
    else:
        print("❌ No se encontró anime de prueba")
except Exception as e:
    print(f"❌ Error en importación: {e}")

# Test 3: Probar anime populares
print("\n3. Probando obtención de anime populares...")
try:
    populares = anilist_api.obtener_anime_popular(per_page=5)
    if populares:
        print(f"✅ Obtenidos {len(populares)} animes populares:")
        for i, anime in enumerate(populares, 1):
            title = anime.get('title', {})
            titulo = title.get('english') or title.get('romaji') or 'Sin título'
            score = anime.get('averageScore', 'N/A')
            popularity = anime.get('popularity', 'N/A')
            print(f"  {i}. {titulo} - Score: {score}, Popularidad: {popularity}")
    else:
        print("❌ No se pudieron obtener animes populares")
except Exception as e:
    print(f"❌ Error al obtener populares: {e}")

# Test 4: Mostrar estadísticas
print("\n4. Estadísticas actuales...")
try:
    total_contenidos = Contenido.objects.count()
    contenidos_anilist = Contenido.objects.filter(anilist_id__isnull=False).count()
    contenidos_manuales = total_contenidos - contenidos_anilist
    
    print(f"📊 Total contenidos: {total_contenidos}")
    print(f"🌐 Desde AniList: {contenidos_anilist}")
    print(f"✋ Creados manualmente: {contenidos_manuales}")
    
    if contenidos_anilist > 0:
        print("\nContenido más reciente de AniList:")
        ultimos = Contenido.objects.filter(
            anilist_id__isnull=False
        ).order_by('-id')[:3]
        
        for contenido in ultimos:
            print(f"  • {contenido.titulo} (AniList ID: {contenido.anilist_id})")
    
except Exception as e:
    print(f"❌ Error al obtener estadísticas: {e}")

print("\n🎉 Pruebas completadas!")
print("\n💡 Para usar la integración:")
print("1. Ve al admin: /admin/anilist/")
print("2. Usa el comando: python manage.py importar_anilist --populares 10")
print("3. Busca específico: python manage.py importar_anilist --buscar 'Attack on Titan'")
print("4. Temporada actual: python manage.py importar_anilist --temporada 15")
