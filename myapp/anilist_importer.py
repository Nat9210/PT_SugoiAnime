"""
Importar contenido desde AniList API
"""
import requests
from typing import Dict, List, Optional
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import Contenido, Categoria, ContenidoCategoria
from .anilist_api import anilist_api
import logging
from urllib.parse import urlparse
import uuid

logger = logging.getLogger(__name__)

class AniListImporter:
    """Importador de contenido desde AniList"""
    
    def __init__(self):
        self.api = anilist_api
        self.categorias_cache = {}
    
    def _obtener_o_crear_categoria(self, nombre_categoria: str) -> Categoria:
        """Obtener o crear una categoría"""
        if nombre_categoria not in self.categorias_cache:
            categoria, created = Categoria.objects.get_or_create(
                nombre=nombre_categoria
            )
            self.categorias_cache[nombre_categoria] = categoria
            if created:
                logger.info(f"Nueva categoría creada: {nombre_categoria}")
        
        return self.categorias_cache[nombre_categoria]
    
    def _descargar_imagen(self, url: str, filename: str) -> Optional[str]:
        """Descargar imagen desde URL"""
        try:
            if not url:
                return None
                
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Generar nombre único para el archivo
            extension = url.split('.')[-1].split('?')[0][:4]  # Obtener extensión
            if extension not in ['jpg', 'jpeg', 'png', 'webp']:
                extension = 'jpg'
            
            unique_filename = f"{filename}_{uuid.uuid4().hex[:8]}.{extension}"
            
            # Guardar archivo
            file_path = default_storage.save(
                f'portadas/{unique_filename}',
                ContentFile(response.content)
            )
            
            logger.info(f"Imagen descargada: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error al descargar imagen {url}: {e}")
            return None
    
    def _limpiar_descripcion(self, descripcion: str) -> str:
        """Limpiar y formatear descripción"""
        if not descripcion:
            return ""
        
        # Remover HTML tags básicos
        import re
        descripcion = re.sub(r'<[^>]+>', '', descripcion)
        # Limitar longitud
        if len(descripcion) > 1000:
            descripcion = descripcion[:997] + "..."
        
        return descripcion.strip()
    
    def _obtener_titulo_preferido(self, titles: Dict, synonyms: List = None) -> str:
        """Obtener el mejor título disponible, priorizando español"""
        synonyms = synonyms or []
        
        # Buscar títulos en español en sinónimos
        for synonym in synonyms:
            if self._es_titulo_español(synonym):
                return synonym
        
        # Verificar si el título inglés contiene indicadores de español
        english_title = titles.get('english', '')
        if english_title and self._es_titulo_español(english_title):
            return english_title
        
        # Prioridad estándar: inglés > romaji > native > userPreferred
        if titles.get('english'):
            return titles['english']
        elif titles.get('romaji'):
            return titles['romaji']
        elif titles.get('native'):
            return titles['native']
        elif titles.get('userPreferred'):
            return titles['userPreferred']
        else:
            return "Título no disponible"
    
    def _es_titulo_español(self, titulo: str) -> bool:
        """Verificar si un título parece estar en español"""
        if not titulo:
            return False
        
        # Palabras indicadoras de español
        indicadores_español = [
            'el ', 'la ', 'los ', 'las ', 'de ', 'del ', 'que ', 'por ', 'para ',
            'con ', 'sin ', 'sobre ', 'entre ', 'durante ', 'después ', 'antes ',
            'muy ', 'más ', 'menos ', 'también ', 'solo ', 'sólo ', 'cuando ',
            'donde ', 'dónde ', 'como ', 'cómo ', 'porque ', 'aunque ', 'mientras ',
            'desde ', 'hasta ', 'hacia ', 'según ', 'contra ', 'bajo ', 'sobre '
        ]
        
        titulo_lower = titulo.lower()
        
        # Verificar si contiene palabras en español
        for indicador in indicadores_español:
            if indicador in titulo_lower:
                return True
        
        # Verificar caracteres específicos del español
        if any(char in titulo for char in ['ñ', 'Ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü']):
            return True
        
        return False
    
    def _convertir_formato_anilist(self, formato_anilist: str) -> str:
        """Convertir formato de AniList a formato local"""
        formato_map = {
            'TV': 'serie',
            'TV_SHORT': 'serie',
            'MOVIE': 'pelicula',
            'SPECIAL': 'serie',
            'OVA': 'serie',
            'ONA': 'serie',
            'MUSIC': 'serie'
        }
        return formato_map.get(formato_anilist, 'serie')
    
    def _obtener_descripcion_preferida(self, anime_data: Dict) -> str:
        """Obtener la mejor descripción disponible, priorizando español"""
        descripcion = anime_data.get('description', '')
        
        # Si no hay descripción, intentar obtener de sinónimos o tags
        if not descripcion or len(descripcion.strip()) < 10:
            # Usar géneros como descripción básica si no hay otra
            genres = anime_data.get('genres', [])
            if genres:
                descripcion = f"Anime de {', '.join(genres[:3])}"
        
        return self._limpiar_descripcion(descripcion)
    
    def importar_anime_desde_anilist(self, anime_data: Dict) -> Optional[Contenido]:
        """Importar un anime específico desde datos de AniList"""
        try:
            # Verificar si ya existe por ID de AniList
            anilist_id = anime_data.get('id')
            if not anilist_id:
                logger.warning("Anime sin ID de AniList")
                return None
            
            # Buscar si ya existe
            existing_content = Contenido.objects.filter(
                anilist_id=anilist_id
            ).first()            
            if existing_content:
                logger.info(f"Anime ya existe: {existing_content.titulo}")
                return existing_content
            
            # Preparar datos
            titles = anime_data.get('title', {})
            synonyms = anime_data.get('synonyms', [])
            titulo = self._obtener_titulo_preferido(titles, synonyms)
            
            descripcion = self._obtener_descripcion_preferida(anime_data)
            
            tipo = self._convertir_formato_anilist(
                anime_data.get('format', 'TV')
            )
            
            # Obtener año
            start_date = anime_data.get('startDate', {})
            año = start_date.get('year') if start_date else None
            
            # Duración
            duracion = anime_data.get('duration') or anime_data.get('episodes', 1) * 24
            
            # Crear contenido
            contenido = Contenido.objects.create(
                titulo=titulo,
                tipo=tipo,
                descripcion=descripcion,
                año=año,
                duracion=duracion,
                anilist_id=anilist_id,
                anilist_score=anime_data.get('averageScore'),
                anilist_popularity=anime_data.get('popularity', 0)
            )
            
            # Descargar imagen de portada
            cover_image = anime_data.get('coverImage', {})
            image_url = (cover_image.get('extraLarge') or 
                        cover_image.get('large') or 
                        cover_image.get('medium'))
            
            if image_url:
                image_path = self._descargar_imagen(
                    image_url, 
                    f"anilist_{anilist_id}"
                )
                if image_path:
                    contenido.imagen_portada = image_path
                    contenido.save()
            
            # Agregar géneros como categorías
            genres = anime_data.get('genres', [])
            for genre in genres:
                categoria = self._obtener_o_crear_categoria(genre)
                ContenidoCategoria.objects.get_or_create(
                    contenido=contenido,
                    categoria=categoria
                )
            
            # Agregar tags importantes como categorías adicionales
            tags = anime_data.get('tags', [])
            for tag in tags[:5]:  # Solo los primeros 5 tags
                if tag.get('rank', 0) > 70:  # Solo tags relevantes
                    tag_name = tag.get('name', '')
                    if tag_name and len(tag_name) < 50:
                        categoria = self._obtener_o_crear_categoria(tag_name)
                        ContenidoCategoria.objects.get_or_create(
                            contenido=contenido,
                            categoria=categoria
                        )
            
            logger.info(f"Anime importado exitosamente: {titulo}")
            return contenido
            
        except Exception as e:
            logger.error(f"Error al importar anime: {e}")
            return None
    
    def buscar_e_importar(self, termino_busqueda: str, max_resultados: int = 10) -> List[Contenido]:
        """Buscar en AniList e importar resultados"""
        try:
            logger.info(f"Buscando en AniList: {termino_busqueda}")
            
            # Buscar en AniList
            resultados = self.api.buscar_anime(
                search_term=termino_busqueda,
                per_page=max_resultados
            )
            
            contenidos_importados = []
            
            for anime_data in resultados:
                contenido = self.importar_anime_desde_anilist(anime_data)
                if contenido:
                    contenidos_importados.append(contenido)
            
            logger.info(f"Importados {len(contenidos_importados)} animes de AniList")
            return contenidos_importados
            
        except Exception as e:
            logger.error(f"Error en búsqueda e importación: {e}")
            return []
    
    def importar_populares(self, cantidad: int = 20) -> List[Contenido]:
        """Importar anime populares actuales"""
        try:
            logger.info(f"Importando {cantidad} animes populares de AniList")
            
            resultados = self.api.obtener_anime_popular(per_page=cantidad)
            
            contenidos_importados = []
            
            for anime_data in resultados:
                contenido = self.importar_anime_desde_anilist(anime_data)
                if contenido:
                    contenidos_importados.append(contenido)
            
            logger.info(f"Importados {len(contenidos_importados)} animes populares")
            return contenidos_importados
            
        except Exception as e:
            logger.error(f"Error al importar populares: {e}")
            return []
    
    def importar_temporada_actual(self, cantidad: int = 20) -> List[Contenido]:
        """Importar anime de la temporada actual"""
        try:
            from datetime import datetime
            
            year = datetime.now().year
            month = datetime.now().month
            
            # Determinar temporada
            if month in [12, 1, 2]:
                season = "WINTER"
            elif month in [3, 4, 5]:
                season = "SPRING"
            elif month in [6, 7, 8]:
                season = "SUMMER"
            else:
                season = "FALL"
            
            logger.info(f"Importando anime de {season} {year}")
            
            resultados = self.api.obtener_anime_temporada(
                year=year,
                season=season,
                per_page=cantidad
            )
            
            contenidos_importados = []
            
            for anime_data in resultados:
                contenido = self.importar_anime_desde_anilist(anime_data)
                if contenido:
                    contenidos_importados.append(contenido)
            
            logger.info(f"Importados {len(contenidos_importados)} animes de temporada")
            return contenidos_importados
            
        except Exception as e:
            logger.error(f"Error al importar temporada: {e}")
            return []
    
    def buscar_e_importar_español(self, termino_busqueda: str, max_resultados: int = 10) -> List[Contenido]:
        """Buscar en AniList con énfasis en contenido en español e importar resultados"""
        try:
            logger.info(f"Buscando contenido en español en AniList: {termino_busqueda}")
            
            # Buscar usando el método especializado en español
            resultados = self.api.buscar_anime_español(
                search_term=termino_busqueda,
                per_page=max_resultados
            )
            
            contenidos_importados = []
            
            for anime_data in resultados:
                contenido = self.importar_anime_desde_anilist(anime_data)
                if contenido:
                    contenidos_importados.append(contenido)
            
            logger.info(f"Importados {len(contenidos_importados)} animes con énfasis en español")
            return contenidos_importados
            
        except Exception as e:
            logger.error(f"Error en búsqueda e importación de contenido español: {e}")
            return []

# Instancia global del importador
anilist_importer = AniListImporter()
