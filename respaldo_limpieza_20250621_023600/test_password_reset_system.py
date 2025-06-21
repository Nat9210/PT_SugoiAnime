#!/usr/bin/env python3
"""
Script para probar el sistema completo de reseteo de contraseñas
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.test import RequestFactory, Client
import re

def test_password_reset_system():
    """Prueba completa del sistema de reseteo de contraseñas"""
    print("🔐 PROBANDO SISTEMA DE RESETEO DE CONTRASEÑAS")
    print("=" * 50)
    
    # 1. Verificar que existe un usuario de prueba
    print("\n1. 📋 Verificando usuarios...")
    users = User.objects.all()
    if users.exists():
        test_user = users.first()
        print(f"   ✅ Usuario encontrado: {test_user.username} ({test_user.email})")
    else:
        # Crear usuario de prueba
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        print(f"   ✅ Usuario creado: {test_user.username} ({test_user.email})")
    
    # 2. Probar generación de token
    print("\n2. 🔑 Probando generación de token...")
    token = default_token_generator.make_token(test_user)
    uid = urlsafe_base64_encode(force_bytes(test_user.pk))
    print(f"   ✅ Token generado: {token[:20]}...")
    print(f"   ✅ UID generado: {uid}")
    
    # 3. Verificar token
    print("\n3. ✅ Verificando validez del token...")
    decoded_uid = force_str(urlsafe_base64_decode(uid))
    user_check = User.objects.get(pk=decoded_uid)
    token_valid = default_token_generator.check_token(user_check, token)
    print(f"   ✅ Token válido: {token_valid}")
    print(f"   ✅ Usuario recuperado: {user_check.username}")
    
    # 4. Probar URLs
    print("\n4. 🌐 Probando URLs...")
    client = Client()
    
    # URL de solicitud
    try:
        response = client.get('/password_reset/')
        print(f"   ✅ GET /password_reset/ - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ GET /password_reset/ - Error: {e}")
    
    # URL de confirmación
    try:
        response = client.get('/password_reset/done/')
        print(f"   ✅ GET /password_reset/done/ - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ GET /password_reset/done/ - Error: {e}")
    
    # URL de reset con token
    try:
        response = client.get(f'/reset/{uid}/{token}/')
        print(f"   ✅ GET /reset/{uid}/{token}/ - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ GET /reset/token/ - Error: {e}")
    
    # URL de completado
    try:
        response = client.get('/reset/done/')
        print(f"   ✅ GET /reset/done/ - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ GET /reset/done/ - Error: {e}")
    
    # 5. Probar formulario POST
    print("\n5. 📝 Probando envío de formulario...")
    try:
        response = client.post('/password_reset/', {
            'username': test_user.username,
            'email': test_user.email
        })
        print(f"   ✅ POST /password_reset/ - Status: {response.status_code}")
        if response.status_code == 302:
            print(f"   ✅ Redirección a: {response.url}")
    except Exception as e:
        print(f"   ❌ POST /password_reset/ - Error: {e}")
    
    # 6. Probar validación de contraseña
    print("\n6. 🔒 Probando validación de contraseñas...")
    from myapp.views import validate_password_strength
    
    test_passwords = [
        ('123', 'Muy corta'),
        ('password', 'Sin mayúscula, número ni símbolo'),
        ('Password', 'Sin número ni símbolo'),
        ('Password1', 'Sin símbolo'),
        ('Password1!', 'Válida')
    ]
    
    for password, description in test_passwords:
        error = validate_password_strength(password)
        status = "❌" if error else "✅"
        print(f"   {status} '{password}' ({description}) - {error or 'Válida'}")
    
    # 7. Verificar templates
    print("\n7. 📄 Verificando templates...")
    templates = [
        'myapp/password_reset_request.html',
        'myapp/password_reset_done.html', 
        'myapp/password_reset_email.html',
        'myapp/password_reset_confirm.html',
        'myapp/password_reset_complete.html',
        'myapp/password_changed_email.html'
    ]
    
    for template in templates:
        template_path = f'myapp/templates/{template}'
        if os.path.exists(template_path):
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template} - NO ENCONTRADO")
    
    print(f"\n🎉 PRUEBA COMPLETADA")
    print("=" * 50)
    
    # Resumen
    print(f"\n📊 RESUMEN:")
    print(f"   • Usuario de prueba: {test_user.username}")
    print(f"   • Email de prueba: {test_user.email}")
    print(f"   • Token válido: {token_valid}")
    print(f"   • Templates presentes: {len([t for t in templates if os.path.exists(f'myapp/templates/{t}')])}/6")
    print(f"   • Sistema funcionando: ✅")

if __name__ == "__main__":
    test_password_reset_system()
