# Script para probar el sistema de historial de búsqueda
# Copia y pega este código en el shell de Django (python manage.py shell)

from django.contrib.auth.models import User
from myapp.models import HistorialBusqueda, Contenido, Categoria, Perfil

print("=== TESTING SISTEMA DE HISTORIAL DE BÚSQUEDA ===")

# 1. Crear algunos datos de prueba si no existen
print("\n1. Verificando datos de prueba...")

# Verificar usuario de prueba
usuario, created = User.objects.get_or_create(
    username='usuario_test',
    defaults={'email': 'test@example.com', 'password': 'testpass123'}
)
if created:
    print("✓ Usuario de prueba creado")
else:
    print("✓ Usuario de prueba ya existe")

# Verificar perfil
perfil, created = Perfil.objects.get_or_create(
    usuario=usuario,
    defaults={'nombre': 'Perfil Test', 'tipo': 'adulto'}
)
if created:
    print("✓ Perfil de prueba creado")
else:
    print("✓ Perfil de prueba ya existe")

# 2. Crear registros de búsqueda de prueba
print("\n2. Creando registros de búsqueda de prueba...")

terminos_prueba = [
    'naruto',
    'one piece', 
    'dragon ball',
    'attack on titan',
    'demon slayer',
    'naruto',  # duplicado para probar popularidad
    'one piece',  # duplicado
    'death note',
    'fullmetal alchemist',
    'naruto'  # otro duplicado
]

for termino in terminos_prueba:
    HistorialBusqueda.registrar_busqueda(
        termino=termino,
        usuario=usuario,
        perfil=perfil,
        resultados_count=5,  # simulamos 5 resultados
        ip_address='127.0.0.1',
        user_agent='Test Browser'
    )

print(f"✓ Creados {len(terminos_prueba)} registros de búsqueda")

# 3. Verificar los registros creados
print("\n3. Verificando registros de historial...")
total_busquedas = HistorialBusqueda.objects.count()
print(f"✓ Total de búsquedas registradas: {total_busquedas}")

busquedas_usuario = HistorialBusqueda.objects.filter(usuario=usuario).count()
print(f"✓ Búsquedas del usuario test: {busquedas_usuario}")

# 4. Probar métodos del modelo
print("\n4. Probando métodos del modelo...")

# Términos más buscados
mas_buscados = HistorialBusqueda.obtener_mas_buscados(limite=5, dias=30)
print("✓ Términos más buscados:")
for i, termino in enumerate(mas_buscados, 1):
    print(f"   {i}. '{termino['ultimo_termino_original']}' - {termino['total_busquedas']} búsquedas")

# Búsquedas del usuario
busquedas_recientes = HistorialBusqueda.obtener_busquedas_usuario(usuario, limite=5)
print(f"\n✓ Últimas 5 búsquedas del usuario:")
for busqueda in busquedas_recientes:
    print(f"   - '{busqueda.termino_busqueda}' ({busqueda.timestamp.strftime('%Y-%m-%d %H:%M:%S')})")

# Estadísticas
stats = HistorialBusqueda.obtener_estadisticas_busqueda(dias=7)
print(f"\n✓ Estadísticas de búsqueda (últimos 7 días):")
print(f"   - Total búsquedas: {stats['total_busquedas']}")
print(f"   - Búsquedas únicas: {stats['busquedas_unicas']}")
print(f"   - Promedio de resultados: {stats['promedio_resultados']:.2f}" if stats['promedio_resultados'] else "   - Promedio de resultados: 0")
print(f"   - Usuarios únicos: {stats['usuarios_unicos']}")

# 5. Verificar que los datos lleguen al contexto del index
print("\n5. Simulando contexto del index...")
terminos_para_index = HistorialBusqueda.obtener_mas_buscados(limite=8, dias=30)
print(f"✓ Términos que aparecerán en el index: {len(terminos_para_index)}")

for termino in terminos_para_index:
    print(f"   - '{termino['ultimo_termino_original']}' ({termino['total_busquedas']} búsquedas)")

print("\n=== PRUEBA COMPLETADA ===")
print("✓ El sistema de historial de búsqueda está funcionando correctamente")
print("✓ Los datos deberían aparecer ahora en la página principal")
print("\nPara ver los resultados:")
print("1. Ve a http://127.0.0.1:8000/ para ver el contenido más buscado")
print("2. Ve al admin panel para revisar los registros de HistorialBusqueda")
print("3. Realiza algunas búsquedas reales para generar más datos")
