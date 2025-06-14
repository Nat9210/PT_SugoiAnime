#!/usr/bin/env python
"""
Script para crear datos de prueba y validar el sistema de estadísticas
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import (
    Contenido, Categoria, ContenidoCategoria, Calificacion, 
    HistorialReproduccion, HistorialBusqueda, Perfil
)

def crear_datos_prueba():
    """Crear datos de prueba para validar estadísticas"""
    print("🔄 Creando datos de prueba...")
    
    # Crear usuarios de prueba
    usuarios = []
    for i in range(5):
        username = f'testuser{i+1}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@test.com',
                'first_name': f'Test{i+1}',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            # Crear perfil
            Perfil.objects.get_or_create(
                usuario=user,
                defaults={'nombre': f'Perfil {i+1}', 'tipo': 'adulto'}
            )
        usuarios.append(user)
    
    # Crear categorías
    categorias_nombres = ['Acción', 'Romance', 'Comedia', 'Drama', 'Aventura']
    categorias = []
    for nombre in categorias_nombres:
        categoria, _ = Categoria.objects.get_or_create(
            nombre=nombre
        )
        categorias.append(categoria)
    
    # Crear contenido de prueba
    contenidos_data = [
        {'titulo': 'Attack on Titan', 'duracion': 24, 'tipo': 'serie'},
        {'titulo': 'Your Name', 'duracion': 106, 'tipo': 'pelicula'},
        {'titulo': 'One Piece', 'duracion': 24, 'tipo': 'serie'},
        {'titulo': 'Spirited Away', 'duracion': 125, 'tipo': 'pelicula'},
        {'titulo': 'Demon Slayer', 'duracion': 24, 'tipo': 'serie'},
        {'titulo': 'Princess Mononoke', 'duracion': 134, 'tipo': 'pelicula'},
        {'titulo': 'Naruto', 'duracion': 23, 'tipo': 'serie'},
        {'titulo': 'Akira', 'duracion': 124, 'tipo': 'pelicula'},
    ]
    
    contenidos = []
    for data in contenidos_data:
        contenido, created = Contenido.objects.get_or_create(
            titulo=data['titulo'],
            defaults={
                'descripcion': f'Descripción de {data["titulo"]}',
                'duracion': data['duracion'],
                'tipo': data['tipo'],
                'año': random.randint(2010, 2024)
            }
        )
        contenidos.append(contenido)
        
        # Asignar categorías aleatorias
        if created:
            cats_asignadas = random.sample(categorias, random.randint(1, 3))
            for cat in cats_asignadas:
                ContenidoCategoria.objects.get_or_create(
                    contenido=contenido,
                    categoria=cat
                )
    
    print(f"✅ Creados {len(contenidos)} contenidos")
      # Crear historial de reproducciones (más visto)
    for contenido in contenidos:
        # Diferentes niveles de popularidad
        if 'Attack on Titan' in contenido.titulo or 'One Piece' in contenido.titulo:
            num_reproducciones = random.randint(50, 100)
        elif 'Your Name' in contenido.titulo or 'Spirited Away' in contenido.titulo:
            num_reproducciones = random.randint(30, 70)
        else:
            num_reproducciones = random.randint(10, 40)
        
        for _ in range(num_reproducciones):
            usuario = random.choice(usuarios)
            perfil = usuario.perfiles.first()
            if perfil:
                HistorialReproduccion.objects.get_or_create(
                    perfil=perfil,
                    contenido=contenido,
                    defaults={
                        'tiempo_reproducido': random.randint(300, 3600),
                        'fecha': datetime.now() - timedelta(
                            days=random.randint(0, 30)
                        )
                    }
                )
    
    print("✅ Creado historial de reproducciones")
    
    # Crear calificaciones (me gusta y rating)
    for contenido in contenidos:
        # Diferentes patrones de calificación
        if 'Attack on Titan' in contenido.titulo:
            # Muy bien valorado
            calificaciones = [4, 5, 5, 4, 5, 3, 4, 5, 5, 4]
        elif 'Your Name' in contenido.titulo:
            # Excelente valoración
            calificaciones = [5, 5, 4, 5, 5, 5, 4, 5, 5, 5]
        elif 'Akira' in contenido.titulo:
            # Valoración mixta
            calificaciones = [3, 4, 2, 5, 3, 4, 2, 3, 4, 3]
        else:
            # Valoración aleatoria
            calificaciones = [random.randint(1, 5) for _ in range(random.randint(5, 15))]
          for i, cal in enumerate(calificaciones):
            usuario = usuarios[i % len(usuarios)]
            perfil = usuario.perfiles.first()
            if perfil:
                Calificacion.objects.get_or_create(
                    perfil=perfil,
                    contenido=contenido,
                    defaults={
                        'calificacion': cal,
                        'fecha': datetime.now() - timedelta(
                            days=random.randint(0, 30)
                        )
                    }
                )
    
    print("✅ Creadas calificaciones")
    
    # Crear historial de búsqueda
    terminos_busqueda = [
        'attack titan', 'your name', 'one piece', 'spirited away',
        'demon slayer', 'naruto', 'akira', 'anime', 'acción',
        'romance', 'comedia', 'aventura', 'ghibli', 'shounen'
    ]
    
    for _ in range(100):  # 100 búsquedas de prueba
        usuario = random.choice(usuarios)
        termino = random.choice(terminos_busqueda)
        
        HistorialBusqueda.objects.create(
            usuario=usuario,
            termino_busqueda=termino,
            resultados_encontrados=random.randint(1, 10),
            fecha_busqueda=datetime.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
        )
    
    print("✅ Creado historial de búsqueda")

def validar_estadisticas():
    """Validar que las estadísticas se calculan correctamente"""
    print("\n📊 Validando estadísticas...")
    
    # Importar las funciones de agregación necesarias
    from django.db.models import Count, Avg, Q
    
    # 1. Términos más buscados
    print("\n1. TÉRMINOS MÁS BUSCADOS:")
    terminos = HistorialBusqueda.obtener_mas_buscados(limite=5, dias=30)
    for i, termino in enumerate(terminos, 1):
        print(f"   {i}. '{termino['termino_normalizado']}' - {termino['total_busquedas']} búsquedas")
    
    # 2. Contenido más visto
    print("\n2. CONTENIDO MÁS VISTO:")
    contenido_mas_visto = Contenido.objects.annotate(
        total_reproducciones=Count('historialreproduccion'),
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion')
    ).filter(
        total_reproducciones__gt=0
    ).order_by('-total_reproducciones')[:5]
    
    for i, contenido in enumerate(contenido_mas_visto, 1):
        rating = contenido.rating_promedio or 0
        print(f"   {i}. '{contenido.titulo}' - {contenido.total_reproducciones} views, "
              f"Rating: {rating:.1f} ({contenido.total_calificaciones} calificaciones)")
    
    # 3. Contenido con más me gusta
    print("\n3. CONTENIDO CON MÁS ME GUSTA:")
    contenido_mas_gustado = Contenido.objects.annotate(
        total_likes=Count('calificacion', filter=Q(calificacion__calificacion__gte=4)),
        total_dislikes=Count('calificacion', filter=Q(calificacion__calificacion__lte=2)),
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion')
    ).filter(
        total_likes__gt=0
    ).order_by('-total_likes', '-rating_promedio')[:5]
    
    for i, contenido in enumerate(contenido_mas_gustado, 1):
        rating = contenido.rating_promedio or 0
        print(f"   {i}. '{contenido.titulo}' - {contenido.total_likes} likes, "
              f"{contenido.total_dislikes} dislikes, Rating: {rating:.1f}")
    
    # 4. Contenido mejor valorado
    print("\n4. CONTENIDO MEJOR VALORADO:")
    contenido_mejor_valorado = Contenido.objects.annotate(
        rating_promedio=Avg('calificacion__calificacion'),
        total_calificaciones=Count('calificacion'),
        total_likes=Count('calificacion', filter=Q(calificacion__calificacion__gte=4))
    ).filter(
        total_calificaciones__gte=3
    ).order_by('-rating_promedio', '-total_calificaciones')[:5]
    
    for i, contenido in enumerate(contenido_mejor_valorado, 1):
        rating = contenido.rating_promedio or 0
        print(f"   {i}. '{contenido.titulo}' - Rating: {rating:.1f} "
              f"({contenido.total_calificaciones} calificaciones, {contenido.total_likes} likes)")

def main():
    """Función principal"""
    print("🚀 Iniciando script de validación de estadísticas")
    print("=" * 50)
    
    try:
        crear_datos_prueba()
        validar_estadisticas()
        
        print("\n" + "=" * 50)
        print("✅ Script completado exitosamente!")
        print("🌐 Ahora puedes visitar el index para ver las estadísticas en acción.")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
