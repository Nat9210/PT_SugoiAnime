# Configuración MySQL para settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sugoianime_db',
        'USER': 'root',  # Tu usuario MySQL
        'PASSWORD': '',  # Tu contraseña MySQL  
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Comandos SQL para crear la base de datos:
"""
-- Conectar a MySQL como root
mysql -u root -p

-- Crear base de datos
CREATE DATABASE sugoianime_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario específico (opcional pero recomendado)
CREATE USER 'sugoianime_user'@'localhost' IDENTIFIED BY 'tu_password_segura';
GRANT ALL PRIVILEGES ON sugoianime_db.* TO 'sugoianime_user'@'localhost';
FLUSH PRIVILEGES;

-- Si usas el usuario específico, actualiza la configuración:
'USER': 'sugoianime_user',
'PASSWORD': 'tu_password_segura',
"""
