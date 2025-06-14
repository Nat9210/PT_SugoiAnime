# settings_mysql.py - Configuración alternativa con MySQL

import os
from .settings import *

# Sobrescribir configuración de base de datos para MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sugoianime_db',
        'USER': 'root',
        'PASSWORD': '',  # Añadir tu contraseña
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Para usar esta configuración:
# python manage.py runserver --settings=sugoianime.settings_mysql
