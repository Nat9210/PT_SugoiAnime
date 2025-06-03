from django.db import models

# Tabla de perfiles dentro de una cuenta de usuario
class Perfil(models.Model):
    TIPO_CHOICES = [
        ('adulto', 'Adulto'),
        ('infantil', 'Infantil'),
    ]

    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='perfiles')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"

# Tabla de categorías
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# Tabla de contenido (series y películas)
class Contenido(models.Model):
    TIPO_CHOICES = [
        ('serie', 'Serie'),
        ('pelicula', 'Película'),
    ]

    titulo = models.CharField(max_length=255, db_index=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, db_index=True)
    descripcion = models.TextField(blank=True)
    año = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    duracion = models.PositiveIntegerField(help_text="Duración en minutos", null=True, blank=True)
    idioma = models.CharField(max_length=50, blank=True)
    imagen_portada = models.ImageField(upload_to='portadas/', null=True, blank=True)
    video_url = models.URLField(max_length=1000, null=True, blank=True)
    categorias = models.ManyToManyField(Categoria, through='ContenidoCategoria', related_name='contenidos')

    class Meta:
        indexes = [
            models.Index(fields=['titulo', 'tipo']),
            models.Index(fields=['año', '-id']),
            models.Index(fields=['-id']),
        ]
        ordering = ['-id']

    def __str__(self):
        return self.titulo

# Relación entre contenido y categorías
class ContenidoCategoria(models.Model):
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

# Tabla de episodios (solo para series)
class Episodio(models.Model):
    serie = models.ForeignKey(Contenido, on_delete=models.CASCADE, limit_choices_to={'tipo': 'serie'})
    temporada = models.PositiveIntegerField()
    numero_episodio = models.PositiveIntegerField()
    titulo = models.CharField(max_length=255)
    duracion = models.PositiveIntegerField(help_text="Duración en minutos")
    video_url = models.URLField(max_length=1000, blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"T{self.temporada}E{self.numero_episodio} - {self.titulo}"
    
    @property
    def video_source(self):
        """Devuelve la fuente de video prioritaria"""
        if self.video_file and self.video_file.name:
            return self.video_file.url
        elif self.video_url:
            return self.video_url
        return ""

# Historial de reproducción por perfil
class HistorialReproduccion(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    episodio = models.ForeignKey(Episodio, on_delete=models.CASCADE, null=True, blank=True)
    tiempo_reproducido = models.PositiveIntegerField(help_text="Segundos")
    fecha = models.DateTimeField(auto_now_add=True)

# Favoritos por perfil
class Favorito(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

# Comentarios y calificaciones por perfil
class Comentario(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    contenido = models.ForeignKey(Contenido, on_delete=models.CASCADE)
    comentario = models.TextField()
    calificacion = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.perfil.nombre} - {self.contenido.titulo} ({self.calificacion}⭐)"
