-- =====================================================
-- ESQUEMA DE BASE DE DATOS SUGOIANIME
-- Generado para crear diagramas MER
-- =====================================================

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS sugoianime_db 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE sugoianime_db;

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
    CONSTRAINT fk_perfil_usuario FOREIGN KEY (usuario_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    INDEX idx_perfil_usuario (usuario_id),
    INDEX idx_perfil_tipo (tipo)
);

-- Tabla de categorías
CREATE TABLE myapp_categoria (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    INDEX idx_categoria_nombre (nombre)
);

-- Tabla principal de contenido (anime/manga)
CREATE TABLE myapp_contenido (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(10) NOT NULL,
    año INT,
    idioma VARCHAR(50),
    duracion INT,
    imagen_portada VARCHAR(100),
    video_url VARCHAR(500),
    anilist_id INT UNIQUE,
    anilist_url VARCHAR(500),
    anilist_score DECIMAL(3,2),
    anilist_popularity INT,
    fecha_importacion DATETIME(6),
    INDEX idx_contenido_titulo (titulo),
    INDEX idx_contenido_tipo (tipo),
    INDEX idx_contenido_año (año),
    INDEX idx_contenido_anilist_id (anilist_id),
    INDEX idx_contenido_popularity (anilist_popularity)
);

-- Tabla de relación contenido-categorías (muchos a muchos)
CREATE TABLE myapp_contenidocategoria (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contenido_id BIGINT NOT NULL,
    categoria_id BIGINT NOT NULL,
    CONSTRAINT fk_cc_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE,
    CONSTRAINT fk_cc_categoria FOREIGN KEY (categoria_id) REFERENCES myapp_categoria(id) ON DELETE CASCADE,
    UNIQUE KEY unique_contenido_categoria (contenido_id, categoria_id),
    INDEX idx_cc_contenido (contenido_id),
    INDEX idx_cc_categoria (categoria_id)
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
    CONSTRAINT fk_episodio_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE,
    INDEX idx_episodio_contenido (contenido_id),
    INDEX idx_episodio_temporada (temporada),
    INDEX idx_episodio_numero (numero_episodio)
);

-- Tabla de historial de reproducción
CREATE TABLE myapp_historialreproduccion (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    contenido_id BIGINT NOT NULL,
    episodio_id BIGINT,
    fecha_reproduccion DATETIME(6) NOT NULL,
    tiempo_reproducido INT DEFAULT 0,
    completado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_hr_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE,
    CONSTRAINT fk_hr_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE,
    CONSTRAINT fk_hr_episodio FOREIGN KEY (episodio_id) REFERENCES myapp_episodio(id) ON DELETE SET NULL,
    INDEX idx_hr_perfil (perfil_id),
    INDEX idx_hr_contenido (contenido_id),
    INDEX idx_hr_fecha (fecha_reproduccion),
    INDEX idx_hr_completado (completado)
);

-- Tabla de favoritos
CREATE TABLE myapp_favorito (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    contenido_id BIGINT NOT NULL,
    fecha_agregado DATETIME(6) NOT NULL,
    CONSTRAINT fk_favorito_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE,
    CONSTRAINT fk_favorito_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE,
    UNIQUE KEY unique_perfil_contenido_favorito (perfil_id, contenido_id),
    INDEX idx_favorito_perfil (perfil_id),
    INDEX idx_favorito_contenido (contenido_id),
    INDEX idx_favorito_fecha (fecha_agregado)
);

-- Tabla de calificaciones (me gusta/no me gusta + estrellas)
CREATE TABLE myapp_calificacion (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    contenido_id BIGINT NOT NULL,
    calificacion INT NOT NULL,
    fecha_calificacion DATETIME(6) NOT NULL,
    CONSTRAINT fk_calificacion_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE,
    CONSTRAINT fk_calificacion_contenido FOREIGN KEY (contenido_id) REFERENCES myapp_contenido(id) ON DELETE CASCADE,
    CONSTRAINT chk_calificacion_rango CHECK (calificacion >= 1 AND calificacion <= 5),
    UNIQUE KEY unique_perfil_contenido_calificacion (perfil_id, contenido_id),
    INDEX idx_calificacion_perfil (perfil_id),
    INDEX idx_calificacion_contenido (contenido_id),
    INDEX idx_calificacion_valor (calificacion),
    INDEX idx_calificacion_fecha (fecha_calificacion)
);

-- Tabla de historial de búsquedas
CREATE TABLE myapp_historialbusqueda (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    perfil_id BIGINT NOT NULL,
    termino VARCHAR(255) NOT NULL,
    fecha_busqueda DATETIME(6) NOT NULL,
    resultados_encontrados INT DEFAULT 0,
    CONSTRAINT fk_hb_perfil FOREIGN KEY (perfil_id) REFERENCES myapp_perfil(id) ON DELETE CASCADE,
    INDEX idx_hb_perfil (perfil_id),
    INDEX idx_hb_termino (termino),
    INDEX idx_hb_fecha (fecha_busqueda)
);

-- Tabla de sesiones de usuario (auditoría)
CREATE TABLE myapp_sesionusuario (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_inicio DATETIME(6) NOT NULL,
    fecha_fin DATETIME(6),
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_sesion_usuario FOREIGN KEY (usuario_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    INDEX idx_sesion_usuario (usuario_id),
    INDEX idx_sesion_activa (activa),
    INDEX idx_sesion_fecha_inicio (fecha_inicio)
);

-- Tabla de accesos fallidos (seguridad)
CREATE TABLE myapp_accesofallido (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    username VARCHAR(150),
    fecha_intento DATETIME(6) NOT NULL,
    user_agent TEXT,
    INDEX idx_acceso_fallido_ip (ip_address),
    INDEX idx_acceso_fallido_fecha (fecha_intento),
    INDEX idx_acceso_fallido_username (username)
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
    timestamp DATETIME(6) NOT NULL,
    CONSTRAINT fk_audit_usuario FOREIGN KEY (usuario_id) REFERENCES auth_user(id) ON DELETE SET NULL,
    INDEX idx_audit_usuario (usuario_id),
    INDEX idx_audit_accion (accion),
    INDEX idx_audit_modelo (modelo),
    INDEX idx_audit_timestamp (timestamp),
    INDEX idx_audit_ip (ip_address)
);

-- =====================================================
-- VISTAS ÚTILES PARA MÉTRICAS
-- =====================================================

-- Vista de contenido con estadísticas
CREATE VIEW vista_contenido_stats AS
SELECT 
    c.id,
    c.titulo,
    c.tipo,
    c.año,
    COUNT(DISTINCT f.id) as total_favoritos,
    COUNT(DISTINCT CASE WHEN cal.calificacion = 5 THEN cal.id END) as total_likes,
    COUNT(DISTINCT CASE WHEN cal.calificacion = 1 THEN cal.id END) as total_dislikes,
    AVG(cal.calificacion) as promedio_calificacion,
    COUNT(DISTINCT hr.perfil_id) as usuarios_han_visto
FROM myapp_contenido c
LEFT JOIN myapp_favorito f ON c.id = f.contenido_id
LEFT JOIN myapp_calificacion cal ON c.id = cal.contenido_id
LEFT JOIN myapp_historialreproduccion hr ON c.id = hr.contenido_id
GROUP BY c.id, c.titulo, c.tipo, c.año;

-- =====================================================
-- DATOS DE EJEMPLO (OPCIONAL)
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
