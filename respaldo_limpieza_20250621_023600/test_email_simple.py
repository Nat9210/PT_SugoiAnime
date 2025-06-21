#!/usr/bin/env python
"""
Script simple para probar el envío de email de password reset
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

def test_send_email():
    print("📧 Probando envío directo de email...")
    
    # Obtener o crear usuario de prueba
    email = "test@example.com"
    try:
        user = User.objects.get(email=email)
        print(f"✅ Usuario encontrado: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username="testuser",
            email=email,
            password="testpass123"
        )
        print(f"✅ Usuario creado: {user.username}")
    
    # Generar token y uid
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # URL de reset
    reset_url = f"http://127.0.0.1:8000/reset/{uid}/{token}/"
    
    print(f"🔗 URL de reset generada: {reset_url}")
    
    # Preparar contenido del email
    subject = "Restablecimiento de contraseña - SugoiAnime"
    message = f"""
    Hola {user.username},
    
    Has solicitado restablecer tu contraseña en SugoiAnime.
    
    Para restablecer tu contraseña, haz clic en el siguiente enlace:
    {reset_url}
    
    Este enlace será válido por 24 horas.
    
    Si no solicitaste este cambio, ignora este mensaje.
    
    Saludos,
    El equipo de SugoiAnime
    """
    
    try:
        # Enviar email
        print("📤 Enviando email...")
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print("✅ Email enviado correctamente!")
        print("📺 Revisa la consola del servidor Django para ver el email")
        
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")

if __name__ == "__main__":
    test_send_email()
