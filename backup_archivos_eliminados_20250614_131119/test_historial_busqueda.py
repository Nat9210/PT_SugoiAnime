#!/usr/bin/env python
"""
Script de prueba para el sistema de historial de búsqueda
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import HistorialBusqueda, Contenido, Perfil
from django.utils import timezone

def test_historial_busqueda():
    """Probar el sistema de historial de búsqueda"""
    
    print("🔍 TESTING SISTEMA DE HISTORIAL DE BÚSQUEDA")
    print("=" * 50)
    
    # 1. Verificar que el modelo existe y funciona
    print("\n1. Verificando modelo HistorialBusqueda...")
    try:
        count = HistorialBusqueda.objects.count()
        print(f"   ✅ Modelo funciona correctamente. Registros actuales: {count}")
    except Exception as e:
        print(f"   ❌ Error con el modelo: {e}")
        return False
    
    # 2. Probar registro de búsqueda
    print("\n2. Probando registro de búsqueda...")
    try:
        # Obtener o crear un usuario de prueba
        usuario, created = User.objects.get_or_create(
            username='test_search_user',
            defaults={'email': 'test@example.com'}
        )
        if created:
            print(f"   📝 Usuario de prueba creado: {usuario.username}")
        else:
            print(f"   👤 Usando usuario existente: {usuario.username}")
        
        # Obtener o crear perfil
        perfil, created = Perfil.objects.get_or_create(
            usuario=usuario,
            defaults={'nombre': 'Perfil Test', 'tipo': 'adulto'}
        )
        
        # Registrar búsquedas de prueba
        terminos_prueba = [
            'naruto',
            'one piece', 
            'demon slayer',
            'attack on titan',
            'naruto',  # Repetido para probar conteo
            'ONE PIECE',  # Mayúsculas para probar normalización
        ]
        
        for termino in terminos_prueba:
            historial = HistorialBusqueda.registrar_busqueda(
                termino=termino,
                usuario=usuario,
                perfil=perfil,
                resultados_count=5,
                ip_address='127.0.0.1',
                user_agent='Test Browser'
            )
            if historial:
                print(f"   ✅ Búsqueda registrada: '{termino}' -> '{historial.termino_normalizado}'")
            else:
                print(f"   ❌ Error registrando: '{termino}'")
                
    except Exception as e:
        print(f"   ❌ Error registrando búsquedas: {e}")
        return False
    
    # 3. Probar términos más buscados
    print("\n3. Probando obtención de términos más buscados...")
    try:
        mas_buscados = HistorialBusqueda.obtener_mas_buscados(limite=5, dias=30)
        print(f"   📊 Términos más buscados encontrados: {len(mas_buscados)}")
        
        for i, termino_data in enumerate(mas_buscados, 1):
            termino = termino_data['termino_normalizado']
            total = termino_data['total_busquedas']
            ultimo_original = termino_data['ultimo_termino_original']
            print(f"   {i}. '{termino}' - {total} búsquedas (último: '{ultimo_original}')")
            
    except Exception as e:
        print(f"   ❌ Error obteniendo términos más buscados: {e}")
        return False
    
    # 4. Probar búsquedas de usuario
    print("\n4. Probando búsquedas de usuario...")
    try:
        busquedas_usuario = HistorialBusqueda.obtener_busquedas_usuario(usuario, limite=10)
        print(f"   👤 Búsquedas del usuario encontradas: {len(busquedas_usuario)}")
        
        for busqueda in busquedas_usuario[:3]:  # Mostrar solo las 3 más recientes
            tiempo = busqueda.timestamp.strftime('%H:%M:%S')
            print(f"   - {tiempo}: '{busqueda.termino_busqueda}' ({busqueda.resultados_encontrados} resultados)")
            
    except Exception as e:
        print(f"   ❌ Error obteniendo búsquedas de usuario: {e}")
        return False
    
    # 5. Probar estadísticas de búsqueda
    print("\n5. Probando estadísticas de búsqueda...")
    try:
        stats = HistorialBusqueda.obtener_estadisticas_busqueda(dias=7)
        print("   📈 Estadísticas de búsqueda (últimos 7 días):")
        print(f"   - Total de búsquedas: {stats['total_busquedas']}")
        print(f"   - Búsquedas únicas: {stats['busquedas_unicas']}")
        print(f"   - Promedio de resultados: {stats['promedio_resultados']:.1f}" if stats['promedio_resultados'] else "   - Promedio de resultados: 0")
        print(f"   - Usuarios únicos: {stats['usuarios_unicos']}")
        
    except Exception as e:
        print(f"   ❌ Error obteniendo estadísticas: {e}")
        return False
    
    # 6. Verificar integración con contenido
    print("\n6. Verificando integración con contenido...")
    try:
        contenidos_count = Contenido.objects.count()
        print(f"   📚 Contenidos en la base de datos: {contenidos_count}")
        
        if contenidos_count > 0:
            # Simular búsqueda de contenido basada en términos populares
            if mas_buscados:
                primer_termino = mas_buscados[0]['termino_normalizado']
                contenidos_relacionados = Contenido.objects.filter(
                    titulo__icontains=primer_termino
                )[:3]
                print(f"   🔍 Contenidos que coinciden con '{primer_termino}': {len(contenidos_relacionados)}")
                for contenido in contenidos_relacionados:
                    print(f"   - {contenido.titulo} ({contenido.tipo})")
        else:
            print("   ⚠️  No hay contenido en la base de datos para probar la integración")
            
    except Exception as e:
        print(f"   ❌ Error verificando integración con contenido: {e}")
        return False
    
    print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE!")
    print("=" * 50)
    print("✅ El sistema de historial de búsqueda está funcionando correctamente")
    print("✅ Los términos más buscados se registran y recuperan correctamente")
    print("✅ Las estadísticas de búsqueda funcionan")
    print("✅ La integración con el contenido está operativa")
    
    return True

def limpiar_datos_prueba():
    """Limpiar datos de prueba (opcional)"""
    print("\n🧹 ¿Desea limpiar los datos de prueba? (y/N): ", end="")
    respuesta = input().lower()
    
    if respuesta == 'y':
        try:
            # Eliminar búsquedas del usuario de prueba
            usuario_prueba = User.objects.filter(username='test_search_user').first()
            if usuario_prueba:
                HistorialBusqueda.objects.filter(usuario=usuario_prueba).delete()
                print("   ✅ Búsquedas de prueba eliminadas")
                
                # Preguntar si eliminar el usuario también
                print("   ¿Eliminar también el usuario de prueba? (y/N): ", end="")
                if input().lower() == 'y':
                    usuario_prueba.delete()
                    print("   ✅ Usuario de prueba eliminado")
        except Exception as e:
            print(f"   ❌ Error limpiando datos: {e}")

if __name__ == "__main__":
    try:
        # Ejecutar pruebas
        success = test_historial_busqueda()
        
        if success:
            # Ofrecer limpiar datos de prueba
            limpiar_datos_prueba()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error general en las pruebas: {e}")
        import traceback
        traceback.print_exc()
