"""
Servicio para consumir la API de AniList
https://anilist.gitbook.io/anilist-apiv2-docs/
"""
import requests
import json
from typing import Dict, List, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AniListAPI:
    """Cliente para la API de AniList GraphQL"""
    
    BASE_URL = "https://graphql.anilist.co"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
    
    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """Realizar una petición GraphQL a AniList"""
        try:
            payload = {
                'query': query,
                'variables': variables or {}
            }
            
            response = self.session.post(
                self.BASE_URL, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"Error en API AniList: {data['errors']}")
                return None
                
            return data.get('data')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con AniList: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar respuesta de AniList: {e}")
            return None
    
    def buscar_anime(self, search_term: str, page: int = 1, per_page: int = 20) -> List[Dict]:
        """Buscar anime por término de búsqueda"""
        query = '''
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                media(search: $search, type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title {
                        romaji
                        english
                        native
                        userPreferred
                    }
                    description(asHtml: false)
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    type
                    format
                    status
                    episodes                    duration
                    chapters
                    volumes
                    genres
                    synonyms
                    source
                    hashtag
                    averageScore
                    meanScore
                    popularity
                    favourites
                    tags {
                        id
                        name
                        description
                        category
                        rank                        isGeneralSpoiler
                        isMediaSpoiler
                        isAdult
                    }
                    relations {
                        edges {
                            id
                            relationType
                            node {
                                id
                                title {
                                    userPreferred
                                }
                                format
                                type
                                status
                            }
                        }
                    }
                    characterPreview: characters(perPage: 6, sort: [ROLE, RELEVANCE, ID]) {
                        edges {
                            id
                            role
                            name
                            voiceActors(language: JAPANESE, sort: [RELEVANCE, ID]) {
                                id
                                name {
                                    userPreferred
                                }
                                language: languageV2
                                image {
                                    large
                                }
                            }
                            node {
                                id
                                name {
                                    userPreferred
                                }
                                image {
                                    large
                                }
                            }
                        }
                    }
                    studios {
                        edges {
                            isMain
                            node {
                                id
                                name
                            }
                        }
                    }
                    coverImage {
                        extraLarge
                        large
                        medium
                        color
                    }
                    bannerImage
                    format
                    episodes
                    duration
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    averageScore
                    meanScore
                    popularity
                    favourites
                    source
                    genres
                    isAdult
                    nextAiringEpisode {
                        airingAt
                        timeUntilAiring
                        episode
                    }
                    streamingEpisodes {
                        title
                        thumbnail
                        url
                        site
                    }
                    trailer {
                        id
                        site
                        thumbnail
                    }
                    externalLinks {
                        id
                        url
                        site
                        siteId
                        type
                        language
                        color
                        icon
                        notes
                        isDisabled
                    }
                }
            }
        }
        '''
        
        variables = {
            'search': search_term,
            'page': page,
            'perPage': per_page
        }
        
        data = self._make_request(query, variables)
        
        if data and 'Page' in data:
            return data['Page']['media']
        return []
    
    def obtener_anime_popular(self, page: int = 1, per_page: int = 20) -> List[Dict]:
        """Obtener anime popular actual"""
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(type: ANIME, sort: POPULARITY_DESC, status: RELEASING) {
                    id
                    title {
                        romaji
                        english
                        native
                        userPreferred
                    }
                    description(asHtml: false)
                    startDate {
                        year
                        month
                        day
                    }
                    episodes
                    duration
                    averageScore
                    meanScore
                    popularity
                    favourites
                    genres
                    coverImage {
                        extraLarge
                        large
                        medium
                        color
                    }
                    bannerImage
                    format
                    status
                    season
                    seasonYear
                    studios {
                        edges {
                            isMain
                            node {
                                name
                            }
                        }
                    }
                    nextAiringEpisode {
                        airingAt
                        timeUntilAiring
                        episode
                    }
                    externalLinks {
                        url
                        site
                        language
                    }
                }
            }
        }
        '''
        
        variables = {
            'page': page,
            'perPage': per_page
        }
        
        data = self._make_request(query, variables)
        
        if data and 'Page' in data:
            return data['Page']['media']
        return []
    
    def obtener_anime_temporada(self, year: int, season: str, page: int = 1, per_page: int = 20) -> List[Dict]:
        """Obtener anime de una temporada específica"""
        query = '''
        query ($season: MediaSeason, $seasonYear: Int, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(season: $season, seasonYear: $seasonYear, type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title {
                        romaji
                        english
                        native
                        userPreferred
                    }
                    description(asHtml: false)
                    startDate {
                        year
                        month
                        day
                    }
                    episodes
                    duration
                    averageScore
                    meanScore
                    popularity
                    favourites
                    genres
                    coverImage {
                        extraLarge
                        large
                        medium
                        color
                    }
                    format
                    status
                    studios {
                        edges {
                            isMain
                            node {
                                name
                            }
                        }
                    }
                }
            }
        }
        '''
        
        variables = {
            'season': season.upper(),
            'seasonYear': year,
            'page': page,
            'perPage': per_page
        }
        
        data = self._make_request(query, variables)
        
        if data and 'Page' in data:
            return data['Page']['media']
        return []
    
    def obtener_anime_por_id(self, anime_id: int) -> Optional[Dict]:
        """Obtener información detallada de un anime por ID"""
        query = '''
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title {
                    romaji
                    english
                    native
                    userPreferred
                }
                description(asHtml: false)
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                episodes
                duration
                averageScore
                meanScore
                popularity
                favourites
                genres
                coverImage {
                    extraLarge
                    large
                    medium
                    color
                }
                bannerImage
                format
                status
                season
                seasonYear
                source
                studios {
                    edges {
                        isMain
                        node {
                            id
                            name
                        }
                    }
                }
                characters {
                    edges {
                        role
                        node {
                            id
                            name {
                                userPreferred
                            }
                            image {
                                large
                            }
                        }
                        voiceActors(language: JAPANESE) {
                            id
                            name {
                                userPreferred
                            }
                            image {
                                large
                            }
                        }
                    }
                }
                trailer {
                    id
                    site
                    thumbnail
                }
                externalLinks {
                    url
                    site
                    language
                    color
                    icon
                }
                streamingEpisodes {
                    title
                    thumbnail
                    url
                    site
                }
                tags {
                    name
                    description
                    category
                    rank
                }
            }
        }
        '''
        
        variables = {'id': anime_id}
        data = self._make_request(query, variables)
        
        if data and 'Media' in data:
            return data['Media']
        return None
    
    def buscar_con_filtros(self, **kwargs) -> List[Dict]:
        """Buscar anime con filtros específicos"""
        query = '''
        query ($search: String, $genre: [String], $year: Int, $season: MediaSeason, $format: MediaFormat, $status: MediaStatus, $sort: [MediaSort], $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(search: $search, genre_in: $genre, seasonYear: $year, season: $season, format: $format, status: $status, type: ANIME, sort: $sort) {
                    id
                    title {
                        romaji
                        english
                        native
                        userPreferred
                    }
                    description(asHtml: false)
                    startDate {
                        year
                    }
                    episodes
                    duration
                    averageScore
                    popularity
                    genres
                    coverImage {
                        large
                        medium
                    }
                    format
                    status
                }
            }
        }
        '''
        
        variables = {
            'search': kwargs.get('search'),
            'genre': kwargs.get('genres'),
            'year': kwargs.get('year'),
            'season': kwargs.get('season'),
            'format': kwargs.get('format'),
            'status': kwargs.get('status'),
            'sort': kwargs.get('sort', ['POPULARITY_DESC']),
            'page': kwargs.get('page', 1),
            'perPage': kwargs.get('per_page', 20)
        }
        
        # Limpiar variables None
        variables = {k: v for k, v in variables.items() if v is not None}
        
        data = self._make_request(query, variables)
        
        if data and 'Page' in data:
            return data['Page']['media']
        return []
    
    def buscar_anime_español(self, search_term: str = None, page: int = 1, per_page: int = 20) -> List[Dict]:
        """Buscar anime con énfasis en contenido en español o popular en comunidades hispanohablantes"""
        
        # Términos adicionales que pueden indicar contenido relevante para hispanohablantes
        terminos_español = []
        if search_term:
            terminos_español = [
                search_term,
                f"{search_term} español",
                f"{search_term} spanish",
                f"{search_term} latino"            ]
        
        query = '''
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                media(search: $search, type: ANIME, sort: [POPULARITY_DESC, SCORE_DESC, FAVOURITES_DESC]) {
                    id
                    title {
                        romaji
                        english
                        native
                        userPreferred
                    }
                    description(asHtml: false)
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    type
                    format
                    status
                    episodes
                    duration
                    chapters
                    volumes
                    genres
                    synonyms
                    source
                    hashtag
                    averageScore
                    meanScore
                    popularity
                    favourites
                    countryOfOrigin
                    coverImage {
                        extraLarge
                        large
                        medium
                        color
                    }
                    bannerImage
                    tags {
                        id
                        name
                        description
                        category
                        rank
                        isGeneralSpoiler
                        isMediaSpoiler
                        isAdult
                    }
                    studios {
                        edges {
                            node {
                                id
                                name
                                isAnimationStudio
                            }
                        }
                    }
                    externalLinks {
                        id
                        url
                        site
                        type
                        language
                    }
                }
            }
        }
        '''
        
        variables = {
            'search': search_term,
            'page': page,
            'perPage': per_page
        }
        
        try:
            data = self._make_request(query, variables)
            if data and 'Page' in data:
                media_list = data['Page']['media']
                
                # Filtrar y priorizar contenido con indicadores de español
                def prioritize_spanish_content(anime):
                    score = 0
                    
                    # Verificar títulos
                    titles = anime.get('title', {})
                    synonyms = anime.get('synonyms', [])
                    
                    for title in [titles.get('english', ''), titles.get('romaji', ''), titles.get('native', '')] + synonyms:
                        if title and self._contains_spanish_indicators(title):
                            score += 10
                    
                    # Verificar descripción
                    description = anime.get('description', '')
                    if description and self._contains_spanish_indicators(description):
                        score += 5
                    
                    # Verificar links externos (plataformas españolas/latinoamericanas)
                    external_links = anime.get('externalLinks', [])
                    for link in external_links:
                        if link.get('language') == 'Spanish' or any(platform in link.get('site', '').lower() 
                                                                 for platform in ['crunchyroll', 'funimation', 'netflix']):
                            score += 3
                    
                    # Verificar tags relevantes
                    tags = anime.get('tags', [])
                    for tag in tags:
                        tag_name = tag.get('name', '').lower()
                        if any(keyword in tag_name for keyword in ['spanish', 'latino', 'dub', 'subtitles']):
                            score += 2
                    
                    return score
                
                # Ordenar por relevancia en español
                media_list_with_scores = [(anime, prioritize_spanish_content(anime)) for anime in media_list]
                media_list_with_scores.sort(key=lambda x: (x[1], x[0].get('popularity', 0)), reverse=True)
                
                return [anime for anime, score in media_list_with_scores]
            
            return []
            
        except Exception as e:
            logger.error(f"Error en búsqueda específica de español: {e}")
            return []
    
    def _contains_spanish_indicators(self, text: str) -> bool:
        """Verificar si un texto contiene indicadores de contenido en español"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Palabras clave en español
        spanish_keywords = [
            'español', 'spanish', 'latino', 'castellano', 'doblado', 'doblaje',
            'subtitulado', 'sub español', 'dub español', 'versión española',
            'el ', 'la ', 'los ', 'las ', 'que ', 'por ', 'para ', 'con ',
            'muy ', 'más ', 'menos ', 'también', 'donde', 'cuando', 'como',
            'porque', 'aunque', 'mientras', 'desde', 'hasta', 'hacia'
        ]
        
        for keyword in spanish_keywords:
            if keyword in text_lower:
                return True
        
        # Caracteres específicos del español
        if any(char in text for char in ['ñ', 'Ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü', '¿', '¡']):
            return True
        
        return False
    
# Instancia global del cliente
anilist_api = AniListAPI()
