#!/usr/bin/env python
"""
Verificar estado del contenido importado
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from myapp.models import Contenido

def verificar_estado():
    """Verificar el estado actual del contenido"""
    total = Contenido.objects.count()
    anilist = Contenido.objects.filter(anilist_id__isnull=False).count()
    locales = total - anilist
    
    print(f"📊 Estado del contenido:")
    print(f"   Total contenidos: {total}")
    print(f"   De AniList: {anilist}")
    print(f"   Locales: {locales}")
    
    print(f"\n🎌 Últimos 5 contenidos de AniList:")
    for c in Contenido.objects.filter(anilist_id__isnull=False).order_by('-id')[:5]:
        print(f"   - {c.titulo} (ID: {c.anilist_id}, Score: {c.anilist_score})")
    
    print(f"\n🔍 Contenidos con términos en español:")
    palabras_español = ['el ', 'la ', 'los ', 'las ', 'de ', 'del ']
    for palabra in palabras_español:
        count = Contenido.objects.filter(titulo__icontains=palabra).count()
        if count > 0:
            print(f"   - Títulos con '{palabra.strip()}': {count}")
            for c in Contenido.objects.filter(titulo__icontains=palabra)[:3]:
                print(f"     * {c.titulo}")

if __name__ == "__main__":
    verificar_estado()
