#!/usr/bin/env python3
"""
Script para configurar la migración de SQLite a MySQL
"""

import os
import django
import json
from django.core.management import call_command
from django.conf import settings

def backup_sqlite_data():
    """Respalda los datos de SQLite"""
    print("📦 Respaldando datos de SQLite...")
    
    # Hacer dump de los datos
    os.system("python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > backup_data.json")
    print("✅ Datos respaldados en backup_data.json")

def create_mysql_config():
    """Crea configuración para MySQL"""
    mysql_config = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'sugoianime_db',
            'USER': 'root',  # Cambiar según tu configuración
            'PASSWORD': 'admin.54',  # Añadir tu contraseña
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
    
    print("🔧 Configuración MySQL sugerida:")
    print(json.dumps(mysql_config, indent=2))
    return mysql_config

def migration_instructions():
    """Muestra instrucciones detalladas"""
    print("\n🚀 INSTRUCCIONES DE MIGRACIÓN:")
    print("="*50)
    
    print("\n1. INSTALAR MYSQL:")
    print("   - Descargar MySQL Server desde https://dev.mysql.com/downloads/mysql/")
    print("   - O usar XAMPP/WAMP que incluye MySQL")
    
    print("\n2. CREAR BASE DE DATOS:")
    print("   mysql -u root -p")
    print("   CREATE DATABASE sugoianime_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("   GRANT ALL PRIVILEGES ON sugoianime_db.* TO 'root'@'localhost';")
    
    print("\n3. ACTUALIZAR SETTINGS.PY:")
    print("   - Reemplazar configuración DATABASES")
    print("   - Añadir credenciales MySQL")
    
    print("\n4. MIGRAR:")
    print("   python manage.py migrate")
    print("   python manage.py loaddata backup_data.json")
    
    print("\n5. VERIFICAR:")
    print("   python manage.py runserver")

if __name__ == "__main__":
    print("🔄 MIGRACIÓN SQLite → MySQL")
    print("="*40)
    
    # Hacer backup
    backup_sqlite_data()
    
    # Mostrar configuración
    create_mysql_config()
    
    # Mostrar instrucciones
    migration_instructions()
