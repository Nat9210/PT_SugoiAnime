#!/usr/bin/env python
"""
Script para validar el sistema de auditoría
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import AuditLog, SesionUsuario, AccesoFallido
from django.utils import timezone
from datetime import datetime, timedelta

def test_audit_system():
    print("🔍 Validando Sistema de Auditoría...")
    print("=" * 50)
    
    # Test 1: Verificar modelos
    print("\n1. Verificando modelos de auditoría...")
    try:
        audit_count = AuditLog.objects.count()
        session_count = SesionUsuario.objects.count()
        failed_count = AccesoFallido.objects.count()
        
        print(f"   ✅ AuditLog: {audit_count} registros")
        print(f"   ✅ SesionUsuario: {session_count} registros")
        print(f"   ✅ AccesoFallido: {failed_count} registros")
    except Exception as e:
        print(f"   ❌ Error en modelos: {e}")
        return False
    
    # Test 2: Crear log de prueba
    print("\n2. Creando log de prueba...")
    try:
        # Obtener o crear usuario de prueba
        user, created = User.objects.get_or_create(
            username='test_audit',
            defaults={'email': 'test@audit.com'}
        )
        if created:
            print(f"   ✅ Usuario de prueba creado: {user.username}")
        else:
            print(f"   ✅ Usuario de prueba encontrado: {user.username}")
        
        # Crear log usando el método estático
        log = AuditLog.log_action(
            accion='TEST',
            usuario=user,
            descripcion='Prueba del sistema de auditoría',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            nivel='INFO'
        )
        print(f"   ✅ Log creado exitosamente: ID {log.id}")
        
    except Exception as e:
        print(f"   ❌ Error creando log: {e}")
        return False
    
    # Test 3: Verificar sesión
    print("\n3. Creando sesión de prueba...")
    try:
        session = SesionUsuario.objects.create(
            usuario=user,
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            fecha_inicio=timezone.now(),
            estado='ACTIVE'
        )
        print(f"   ✅ Sesión creada exitosamente: ID {session.id}")
        
    except Exception as e:
        print(f"   ❌ Error creando sesión: {e}")
        return False
    
    # Test 4: Verificar acceso fallido
    print("\n4. Creando acceso fallido de prueba...")
    try:
        failed = AccesoFallido.objects.create(
            username_intentado='usuario_falso',
            ip_address='192.168.1.100',
            user_agent='Malicious Agent',
            fecha_intento=timezone.now(),
            intentos_fallidos=3
        )
        print(f"   ✅ Acceso fallido creado exitosamente: ID {failed.id}")
        
    except Exception as e:
        print(f"   ❌ Error creando acceso fallido: {e}")
        return False
    
    # Test 5: Verificar estadísticas
    print("\n5. Verificando estadísticas...")
    try:
        # Contar logs recientes
        ahora = timezone.now()
        hace_24h = ahora - timedelta(hours=24)
        
        logs_24h = AuditLog.objects.filter(fecha_hora__gte=hace_24h).count()
        sesiones_activas = SesionUsuario.objects.filter(estado='ACTIVE').count()
        accesos_fallidos_24h = AccesoFallido.objects.filter(fecha_intento__gte=hace_24h).count()
        
        print(f"   ✅ Logs últimas 24h: {logs_24h}")
        print(f"   ✅ Sesiones activas: {sesiones_activas}")
        print(f"   ✅ Accesos fallidos 24h: {accesos_fallidos_24h}")
        
    except Exception as e:
        print(f"   ❌ Error en estadísticas: {e}")
        return False
    
    # Test 6: Limpiar datos de prueba
    print("\n6. Limpiando datos de prueba...")
    try:
        # Solo eliminar los que acabamos de crear
        AuditLog.objects.filter(usuario=user, accion='TEST').delete()
        SesionUsuario.objects.filter(usuario=user, ip_address='127.0.0.1').delete()
        AccesoFallido.objects.filter(username_intentado='usuario_falso').delete()
        
        # Eliminar usuario de prueba solo si lo creamos
        if created:
            user.delete()
            print("   ✅ Usuario de prueba eliminado")
        
        print("   ✅ Datos de prueba limpiados")
        
    except Exception as e:
        print(f"   ❌ Error limpiando datos: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Sistema de auditoría validado exitosamente!")
    return True

if __name__ == "__main__":
    test_audit_system()
