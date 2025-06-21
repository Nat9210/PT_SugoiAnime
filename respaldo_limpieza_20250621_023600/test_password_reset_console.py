#!/usr/bin/env python
"""
Script para probar el sistema de password reset y verificar 
que el enlace aparezca en la consola
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse
from django.test import Client
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

def test_password_reset_flow():
    print("🔍 Probando el flujo completo de password reset...")
    
    # Crear usuario de prueba si no existe
    email = "test@example.com"
    username = "testuser"
    
    try:
        user = User.objects.get(email=email)
        print(f"✅ Usuario encontrado: {user.username} ({user.email})")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            email=email,
            password="testpass123"
        )
        print(f"✅ Usuario creado: {user.username} ({user.email})")
    
    # Cliente para simular requests
    client = Client()
    
    # 1. Solicitar reset de password
    print("\n📧 Enviando solicitud de password reset...")
    response = client.post('/password_reset/', {
        'email': email
    })
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Redirección exitosa a password_reset_done")
        print(f"Redirect URL: {response.url}")
    else:
        print("❌ Error en la solicitud")
        print(f"Response content: {response.content.decode()}")
    
    # 2. Generar enlace manualmente para mostrar formato
    print("\n🔗 Generando enlace de reset manually:")
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = f"http://127.0.0.1:8000/reset/{uid}/{token}/"
    print(f"Enlace de reset: {reset_url}")
    
    # 3. Verificar configuración de email
    print("\n⚙️ Configuración de email:")
    from django.conf import settings
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')}")
    
    print("\n✅ Test completado. Revisa la consola del servidor Django para ver el email!")

if __name__ == "__main__":
    test_password_reset_flow()
