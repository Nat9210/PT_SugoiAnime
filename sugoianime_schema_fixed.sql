-- =====================================================
-- ESQUEMA DE BASE DE DATOS SUGOIANIME (CORREGIDO)
-- Compatible con MySQL Workbench y dbdiagram.io
-- =====================================================

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS sugoianime_db 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE sugoianime_db;

-- =====================================================
-- TABLA DE USUARIOS DJANGO (REFERENCIA)
-- =====================================================
-- Nota: Django incluye esta tabla automáticamente
CREATE TABLE auth_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    date_joined DATETIME NOT NULL,
    last_login DATETIME
);

-- =====================================================
-- TABLAS PRINCIPALES
-- =====================================================

-- Tabla de perfiles de usuario
CREATE TABLE myapp_perfil (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    avatar VARCHAR(100),
    usuario_id INT NOT NULL,
    KEY idx_perfil_usuario (usuario_id),
    KEY idx_perfil_tipo (tipo),
    CONSTRAINT fk_perfil_usuario FOREIGN KEY (usuario_id) REFERENCES auth_user(id) ON DELETE CASCADE
);

-- Tabla de categorías
CREATE TABLE myapp_categoria (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    KEY idx_categoria_nombre (nombre)
);

-- Tabla principal de contenido (anime/manga)
CREATE TABLE myapp_contenido (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(10) NOT NULL,
    anio INT,  -- Cambiado de 'año' por compatibilidad
    idioma VARCHAR(50),
    duracion INT,
    imagen_portada VARCHAR(100),
    video_url VARCHAR(500),
    anilist_id INT UNIQUE,
    anilist_url VARCHAR(500),
    anilist_score DECIMAL(3,2),
    anilist_popularity INT,
    fecha_importacion DATETIME,  -- Cambiado DATETIME(6) por compatibilidad
    KEY idx_contenido_titulo (titulo),
    KEY idx_contenido_tipo (tipo),
    KEY idx_contenido_anio (anio),
    KEY idx_contenido_anilist_id (anilist_id),
    KEY idx_contenido_popularity (anilist_popularity)
);

-- Tabla de relación contenido-categorías (muchos a muchos)
CREATE TABLE myapp_contenidocategoria (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contenido_id BIGINT NOT NULL,
    categoria_id BIGINT NOT NULL,
    UNIQUE KEY unique_contenido_categoria (contenido_id, categoria_id),
    KEY idx_cc_contenido (contenido_id),
    KEY idx_cc_categoria (categoria_id),
    CONSTRAINT fk_cc_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE,
    CONSTRAINT fk_cc_categoria FOREIGN KEY (categoria_id) REFERENCES myapp_categoria(id) ON DELETE CASCADE
);

-- Tabla de episodios
CREATE TABLE myapp_episodio (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contenido_id BIGINT NOT NULL,
    temporada INT NOT NULL DEFAULT 1,
    numero_episodio INT NOT NULL,
    titulo VARCHAR(255),
    descripcion TEXT,
    duracion INT,
    video_url VARCHAR(500),
    video_file VARCHAR(100),
    KEY idx_episodio_contenido (contenido_id),
    KEY idx_episodio_temporada (temporada),
    KEY idx_episodio_numero (numero_episodio),
    CONSTRAINT fk_episodio_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE
);

-- Tabla de historial de reproducción
CREATE TABLE myapp_historialreproduccion (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    contenido_id BIGINT NOT NULL,
    episodio_id BIGINT,
    fecha_reproduccion DATETIME NOT NULL,
    tiempo_reproducido INT DEFAULT 0,
    completado BOOLEAN NOT NULL DEFAULT FALSE,
    KEY idx_hr_perfil (perfil_id),
    KEY idx_hr_contenido (contenido_id),
    KEY idx_hr_fecha (fecha_reproduccion),
    KEY idx_hr_completado (completado),
    CONSTRAINT fk_hr_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE,
    CONSTRAINT fk_hr_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE,
    CONSTRAINT fk_hr_episodio FOREIGN KEY (episodio_id) REFERENCES myapp_episodio(id) ON DELETE SET NULL
);

-- Tabla de favoritos
CREATE TABLE myapp_favorito (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    contenido_id BIGINT NOT NULL,
    fecha_agregado DATETIME NOT NULL,
    UNIQUE KEY unique_perfil_contenido_favorito (perfil_id, contenido_id),
    KEY idx_favorito_perfil (perfil_id),
    KEY idx_favorito_contenido (contenido_id),
    KEY idx_favorito_fecha (fecha_agregado),
    CONSTRAINT fk_favorito_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE,
    CONSTRAINT fk_favorito_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE
);

-- Tabla de calificaciones (me gusta/no me gusta + estrellas)
CREATE TABLE myapp_calificacion (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    contenido_id BIGINT NOT NULL,
    calificacion INT NOT NULL,
    fecha_calificacion DATETIME NOT NULL,
    UNIQUE KEY unique_perfil_contenido_calificacion (perfil_id, contenido_id),
    KEY idx_calificacion_perfil (perfil_id),
    KEY idx_calificacion_contenido (contenido_id),
    KEY idx_calificacion_valor (calificacion),
    KEY idx_calificacion_fecha (fecha_calificacion),
    CONSTRAINT chk_calificacion_rango CHECK (calificacion >= 1 AND calificacion <= 5),
    CONSTRAINT fk_calificacion_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE,
    CONSTRAINT fk_calificacion_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE
);

-- Tabla de historial de búsquedas
CREATE TABLE myapp_historialbusqueda (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    termino VARCHAR(255) NOT NULL,
    fecha_busqueda DATETIME NOT NULL,
    resultados_encontrados INT DEFAULT 0,
    KEY idx_hb_perfil (perfil_id),
    KEY idx_hb_termino (termino),
    KEY idx_hb_fecha (fecha_busqueda),
    CONSTRAINT fk_hb_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE
);

-- Tabla de sesiones de usuario (auditoría)
CREATE TABLE myapp_sesionusuario (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_inicio DATETIME NOT NULL,
    fecha_fin DATETIME,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    KEY idx_sesion_usuario (usuario_id),
    KEY idx_sesion_activa (activa),
    KEY idx_sesion_fecha_inicio (fecha_inicio),
    CONSTRAINT fk_sesion_usuario FOREIGN KEY (usuario_id) REFERENCES auth_user(id) ON DELETE CASCADE
);

-- Tabla de accesos fallidos (seguridad)
CREATE TABLE myapp_accesofallido (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    username VARCHAR(150),
    fecha_intento DATETIME NOT NULL,
    user_agent TEXT,
    KEY idx_acceso_fallido_ip (ip_address),
    KEY idx_acceso_fallido_fecha (fecha_intento),
    KEY idx_acceso_fallido_username (username)
);

-- Tabla de logs de auditoría
CREATE TABLE myapp_auditlog (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(100) NOT NULL,
    modelo VARCHAR(100),
    objeto_id VARCHAR(100),
    detalles TEXT,
    ip_address VARCHAR(45),
    timestamp_log DATETIME NOT NULL,  -- Cambiado de 'timestamp' por palabra reservada
    KEY idx_audit_usuario (usuario_id),
    KEY idx_audit_accion (accion),
    KEY idx_audit_modelo (modelo),
    KEY idx_audit_timestamp (timestamp_log),
    KEY idx_audit_ip (ip_address),
    CONSTRAINT fk_audit_usuario FOREIGN KEY (usuario_id) REFERENCES auth_user(id) ON DELETE SET NULL
);

-- =====================================================
-- DATOS DE EJEMPLO
-- =====================================================

-- Insertar categorías básicas
INSERT INTO myapp_categoria (nombre, descripcion) VALUES
('Acción', 'Anime con escenas de combate y aventura'),
('Romance', 'Historias centradas en relaciones amorosas'),
('Comedia', 'Anime divertido y humorístico'),
('Drama', 'Historias emotivas y profundas'),
('Fantasía', 'Mundos mágicos y sobrenaturales'),
('Sci-Fi', 'Ciencia ficción y tecnología'),
('Slice of Life', 'Historias de la vida cotidiana'),
('Thriller', 'Suspense y misterio'),
('Horror', 'Anime de terror y miedo'),
('Sports', 'Deportes y competencias');

-- =====================================================
-- COMENTARIOS SOBRE LA ESTRUCTURA
-- =====================================================

/*
CORRECCIONES REALIZADAS:

1. DATETIME(6) → DATETIME
   - Algunos parsers no soportan microsegundos

2. año → anio  
   - Evitar caracteres especiales en nombres de columna

3. timestamp → timestamp_log
   - 'timestamp' es palabra reservada en MySQL

4. INDEX → KEY
   - Sintaxis más compatible

5. Orden de constraints
   - FOREIGN KEY al final de cada tabla

6. Tabla auth_user incluida
   - Para referencias completas

RELACIONES PRINCIPALES:
- auth_user → myapp_perfil (1:N)
- myapp_contenido ↔ myapp_categoria (N:M) via myapp_contenidocategoria  
- myapp_contenido → myapp_episodio (1:N)
- myapp_perfil → myapp_calificacion/favorito/historial (1:N)

LÓGICA DE CALIFICACIONES:
- calificacion = 5: "Me gusta" ⭐⭐⭐⭐⭐
- calificacion = 1: "No me gusta" ⭐
*/
