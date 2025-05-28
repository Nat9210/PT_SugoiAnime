from django import template
import re

register = template.Library()

def extract_youtube_id(url):
    """
    Extrae el ID de un video de YouTube desde varias formas de URL.
    """
    # youtu.be/VIDEOID
    match = re.match(r'.*youtu\.be/([^?&/]+)', url)
    if match:
        return match.group(1)
    # youtube.com/watch?v=VIDEOID
    match = re.match(r'.*youtube\.com/watch\?v=([^?&/]+)', url)
    if match:
        return match.group(1)
    # youtube.com/embed/VIDEOID
    match = re.match(r'.*youtube\.com/embed/([^?&/]+)', url)
    if match:
        return match.group(1)
    # Si no coincide, devolver la url original (no recomendado)
    return url

@register.filter
def youtube_id(url):
    return extract_youtube_id(url)
