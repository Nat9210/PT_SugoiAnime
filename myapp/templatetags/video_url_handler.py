"""
Utilidades para manejar videos tanto de static como de media
"""
from django import template
from django.conf import settings
from django.templatetags.static import static
import os
from urllib.parse import urlparse

register = template.Library()

@register.filter
def get_correct_video_url(url):
    """
    Determina la URL correcta para un video, ya sea desde media o desde static
    """
    if not url:
        return ''
    
    # Si es una URL externa, devolverla tal cual
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    # Si el archivo existe en static/myapp/videos/, usar static
    static_path = f'myapp/videos/{os.path.basename(url)}'
    static_file_path = os.path.join(settings.STATICFILES_DIRS[0], 'myapp', 'videos', os.path.basename(url))
    
    if os.path.exists(static_file_path):
        return static(static_path)
    
    # Si no, asumir que está en media
    return url
