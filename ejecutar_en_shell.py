# -*- coding: utf-8 -*-
# Script para ejecutar en el shell de Django
# python manage.py shell < este_archivo.py

from django.contrib.auth.models import User
from myapp.models import Contenido, Categoria, ContenidoCategoria, Calificacion, HistorialReproduccion, HistorialBusqueda, Perfil
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import random

print("Iniciando creacion de datos de prueba...")

# Crear usuarios de prueba
usuarios = []
for i in range(3):
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

print(f"Creados {len(usuarios)} usuarios")

# Crear categorias
categorias_nombres = ['Accion', 'Romance', 'Comedia', 'Drama']
categorias = []
for nombre in categorias_nombres:
    categoria, _ = Categoria.objects.get_or_create(nombre=nombre)
    categorias.append(categoria)

print(f"Creadas {len(categorias)} categorias")

# Crear contenido de prueba
contenidos_data = [
    {'titulo': 'Attack on Titan', 'duracion': 24, 'tipo': 'serie'},
    {'titulo': 'Your Name', 'duracion': 106, 'tipo': 'pelicula'},
    {'titulo': 'One Piece', 'duracion': 24, 'tipo': 'serie'},
    {'titulo': 'Demon Slayer', 'duracion': 24, 'tipo': 'serie'},
    {'titulo': 'Spirited Away', 'duracion': 125, 'tipo': 'pelicula'},
    {'titulo': 'Naruto', 'duracion': 23, 'tipo': 'serie'},
]

contenidos = []
for data in contenidos_data:
    contenido, created = Contenido.objects.get_or_create(
        titulo=data['titulo'],
        defaults={
            'descripcion': f'Descripcion de {data["titulo"]}',
            'duracion': data['duracion'],
            'tipo': data['tipo'],
            'año': random.randint(2015, 2024)
        }
    )
    contenidos.append(contenido)
    
    # Asignar categorias aleatorias
    if created:
        cats_asignadas = random.sample(categorias, 2)
        for cat in cats_asignadas:
            ContenidoCategoria.objects.get_or_create(
                contenido=contenido,
                categoria=cat
            )

print(f"Creados {len(contenidos)} contenidos")

# Crear historial de reproducciones
for contenido in contenidos:
    # Attack on Titan y One Piece mas populares
    if 'Attack' in contenido.titulo or 'One Piece' in contenido.titulo:
        num_reproducciones = 25
    elif 'Your Name' in contenido.titulo or 'Spirited' in contenido.titulo:
        num_reproducciones = 20
    else:
        num_reproducciones = 12
    
    for _ in range(num_reproducciones):
        usuario = random.choice(usuarios)
        perfil = usuario.perfiles.first()
        if perfil:
            HistorialReproduccion.objects.get_or_create(
                perfil=perfil,
                contenido=contenido,                defaults={
                    'tiempo_reproducido': random.randint(300, 3600),
                    'fecha': timezone.now() - timedelta(days=random.randint(0, 15))
                }
            )

print("Creado historial de reproducciones")

# Crear calificaciones
for contenido in contenidos:
    if 'Your Name' in contenido.titulo:
        calificaciones = [5, 5, 4, 5, 5, 4, 5]  # Excelente rating
    elif 'Attack' in contenido.titulo:
        calificaciones = [4, 5, 4, 5, 4, 5, 4]  # Muy bueno
    elif 'Spirited' in contenido.titulo:
        calificaciones = [5, 4, 5, 5, 4, 5]  # Excelente
    elif 'One Piece' in contenido.titulo:
        calificaciones = [4, 4, 5, 4, 3, 4, 5]  # Bueno
    else:
        calificaciones = [3, 4, 3, 4, 3, 2, 4]  # Regular
    
    for i, cal in enumerate(calificaciones):
        usuario = usuarios[i % len(usuarios)]
        perfil = usuario.perfiles.first()
        if perfil:
            Calificacion.objects.get_or_create(
                perfil=perfil,
                contenido=contenido,                defaults={
                    'calificacion': cal,
                    'fecha': timezone.now() - timedelta(days=random.randint(0, 15))
                }
            )

print("Creadas calificaciones")

# Crear historial de busqueda
terminos = ['attack titan', 'your name', 'one piece', 'anime', 'accion', 'spirited away', 'demon slayer', 'naruto']
for _ in range(50):
    usuario = random.choice(usuarios)
    termino = random.choice(terminos)
    
    HistorialBusqueda.objects.create(
        usuario=usuario,
        termino_busqueda=termino,
        termino_normalizado=termino.lower().strip(),
        resultados_encontrados=random.randint(1, 8),
        ip_address='127.0.0.1',
        user_agent='Mozilla/5.0 (Test Browser)',
        timestamp=timezone.now() - timedelta(
            days=random.randint(0, 15),
            hours=random.randint(0, 23)
        )
    )

print("Creado historial de busqueda")

# Validar estadisticas
print("\nVALIDANDO ESTADISTICAS:")

# 1. Terminos mas buscados
print("\n1. TERMINOS MAS BUSCADOS:")
terminos = HistorialBusqueda.obtener_mas_buscados(limite=5, dias=30)
for i, termino in enumerate(terminos, 1):
    print(f"   {i}. '{termino['termino_normalizado']}' - {termino['total_busquedas']} busquedas")

# 2. Contenido mas visto
print("\n2. CONTENIDO MAS VISTO:")
contenido_mas_visto = Contenido.objects.annotate(
    total_reproducciones=Count('historialreproduccion'),
    rating_promedio=Avg('calificacion__calificacion'),
    total_calificaciones=Count('calificacion')
).filter(
    total_reproducciones__gt=0
).order_by('-total_reproducciones')[:5]

for i, contenido in enumerate(contenido_mas_visto, 1):
    rating = contenido.rating_promedio or 0
    print(f"   {i}. '{contenido.titulo}' - {contenido.total_reproducciones} views, Rating: {rating:.1f}")

# 3. Contenido con mas me gusta
print("\n3. CONTENIDO CON MAS ME GUSTA:")
contenido_mas_gustado = Contenido.objects.annotate(
    total_likes=Count('calificacion', filter=Q(calificacion__calificacion__gte=4)),
    total_dislikes=Count('calificacion', filter=Q(calificacion__calificacion__lte=2)),
    rating_promedio=Avg('calificacion__calificacion')
).filter(
    total_likes__gt=0
).order_by('-total_likes', '-rating_promedio')[:5]

for i, contenido in enumerate(contenido_mas_gustado, 1):
    rating = contenido.rating_promedio or 0
    print(f"   {i}. '{contenido.titulo}' - {contenido.total_likes} likes, {contenido.total_dislikes} dislikes, Rating: {rating:.1f}")

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
    print(f"   {i}. '{contenido.titulo}' - Rating: {rating:.1f} ({contenido.total_calificaciones} calificaciones, {contenido.total_likes} likes)")

print("\nDatos de prueba creados exitosamente!")
print("Ahora puedes visitar el index para ver las estadisticas funcionando.")
print("También puedes ejecutar el servidor con: python manage.py runserver")
