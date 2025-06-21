#!/usr/bin/env python
"""
Script para probar visualmente el nuevo diseño de password_reset_done
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

def test_password_reset_visual():
    """
    Prueba el flujo de password reset para ver la página mejorada
    """
    print("🔧 Iniciando prueba visual de password reset...")
    
    client = Client()
    
    # Crear un usuario de prueba
    user = User.objects.create_user(
        username='test_visual',
        email='test@sugoianime.com',
        password='password123'
    )
    print(f"✅ Usuario creado: {user.username}")
    
    # Solicitar reset de password
    reset_url = reverse('password_reset_request')
    response = client.post(reset_url, {
        'email': 'test@sugoianime.com'
    })
    
    print(f"📧 Solicitud de reset enviada - Status: {response.status_code}")
    
    if response.status_code == 302:  # Redirect esperado
        print("✅ Redirect correcto a página de confirmación")
        
        # Obtener la URL de la página de confirmación
        done_url = reverse('password_reset_done')
        response = client.get(done_url)
        
        print(f"🎨 Página de confirmación cargada - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ ¡Página de confirmación carga correctamente!")
            print(f"🌐 URL para ver en navegador: http://127.0.0.1:8000{done_url}")
            print("\n📋 Instrucciones:")
            print("1. Ve a http://127.0.0.1:8000/password_reset/")
            print("2. Ingresa un email (puede ser ficticio)")
            print("3. Verás la nueva página mejorada de confirmación")
        else:
            print(f"❌ Error cargando página: {response.status_code}")
    else:
        print(f"❌ Error en solicitud: {response.status_code}")
    
    # Limpiar
    user.delete()
    print("🧹 Usuario de prueba eliminado")

if __name__ == "__main__":
    test_password_reset_visual()
    print("\n🎉 ¡Prueba completada! Ve al navegador para ver el nuevo diseño.")
