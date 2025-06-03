# Utilitarios para el manejo de videos
from django import template
import re
from urllib.parse import urlparse

register = template.Library()

@register.filter
def get_video_type(url):
    """
    Determina el tipo de video basado en la URL.
    """
    if not url:
        return 'unknown'
        
    # Extraer la extensión del archivo de la URL
    path = urlparse(url).path
    ext = path.split('.')[-1].lower() if '.' in path else ''
    
    # Mapeo de extensiones a tipos MIME
    video_types = {
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'ogg': 'video/ogg',
        'mov': 'video/quicktime',
        'avi': 'video/x-msvideo',
        'flv': 'video/x-flv',
        'wmv': 'video/x-ms-wmv',
        'm4v': 'video/mp4',
        'mkv': 'video/x-matroska'
    }
    
    return video_types.get(ext, 'video/mp4')  # Por defecto mp4

@register.filter
def is_s3_url(url):
    """
    Determina si una URL es de Amazon S3.
    """
    if not url:
        return False
        
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc.lower()
    
    # Patrones comunes de S3 y CloudFront
    s3_patterns = [
        'amazonaws.com',
        's3.amazon.com',
        's3.amazonaws.com',
        'cloudfront.net'
    ]
    
    return any(pattern in hostname for pattern in s3_patterns)

@register.filter
def get_video_resolution(url):
    """
    Intenta extraer la resolución del video de la URL.
    """
    resolutions = ['4k', '1080p', '720p', '480p', '360p', '240p']
    
    for res in resolutions:
        if res in url.lower():
            return res
    
    return 'auto'

@register.filter
def clean_url(url):
    """
    Limpia la URL de parámetros innecesarios.
    """
    if not url:
        return ''
        
    parsed_url = urlparse(url)
    clean = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    return clean
