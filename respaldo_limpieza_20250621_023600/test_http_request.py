#!/usr/bin/env python
"""
Script para hacer una solicitud HTTP real al servidor Django corriendo
para probar el password reset y ver la actividad en el terminal del servidor
"""
import requests
import time

def test_password_reset_real():
    print("🌐 Haciendo solicitud HTTP real al servidor Django...")
    
    server_url = "http://127.0.0.1:8000"
    
    try:
        # 1. Primero obtener el formulario para obtener el CSRF token
        print("📋 Obteniendo formulario de password reset...")
        session = requests.Session()
        response = session.get(f"{server_url}/password_reset/")
        
        if response.status_code == 200:
            print("✅ Formulario obtenido correctamente")
            
            # Buscar el CSRF token en el HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            
            if csrf_token:
                csrf_value = csrf_token.get('value')
                print(f"🔐 CSRF token obtenido: {csrf_value[:20]}...")
                
                # 2. Enviar solicitud de password reset
                print("📧 Enviando solicitud de password reset...")
                data = {
                    'email': 'test@example.com',
                    'csrfmiddlewaretoken': csrf_value
                }
                
                response = session.post(f"{server_url}/password_reset/", data=data)
                
                if response.status_code == 302:
                    print("✅ Solicitud enviada correctamente!")
                    print(f"🔄 Redirección a: {response.headers.get('Location', 'No location')}")
                    print("📺 Revisa la terminal del servidor Django - debería mostrar el email ahí")
                else:
                    print(f"❌ Error en la solicitud: {response.status_code}")
                    print(f"Response: {response.text[:500]}...")
            else:
                print("❌ No se pudo encontrar el CSRF token")
        else:
            print(f"❌ Error al obtener el formulario: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor. Asegúrate de que esté corriendo en http://127.0.0.1:8000")
    except ImportError:
        print("❌ BeautifulSoup no está instalado. Instalando...")
        import subprocess
        subprocess.run(["pip", "install", "beautifulsoup4"], check=True)
        print("✅ BeautifulSoup instalado. Ejecuta el script nuevamente.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_password_reset_real()
