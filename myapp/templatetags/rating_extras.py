from django import template
from django.utils.safestring import mark_safe
import math

register = template.Library()

@register.filter
def rating_stars(rating):
    """Convierte un rating numérico en estrellas visuales"""
    if not rating:
        return mark_safe('<span class="text-muted">Sin calificar</span>')
    
    rating = float(rating)
    full_stars = int(rating)
    half_star = rating - full_stars >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    stars_html = ''
    
    # Estrellas completas
    for i in range(full_stars):
        stars_html += '<i class="fa fa-star text-warning"></i>'
    
    # Media estrella
    if half_star:
        stars_html += '<i class="fa fa-star-half-o text-warning"></i>'
    
    # Estrellas vacías
    for i in range(empty_stars):
        stars_html += '<i class="fa fa-star-o text-muted"></i>'
    
    # Agregar el número
    stars_html += f' <span class="rating-number">({rating:.1f})</span>'
    
    return mark_safe(stars_html)

@register.filter
def format_number(number):
    """Formatea números grandes con K, M, etc."""
    if not number:
        return '0'
    
    number = int(number)
    
    if number >= 1000000:
        return f'{number/1000000:.1f}M'
    elif number >= 1000:
        return f'{number/1000:.1f}K'
    else:
        return str(number)

@register.filter
def percentage(value, total):
    """Calcula el porcentaje de value respecto a total"""
    if not total or total == 0:
        return 0
    return round((value / total) * 100, 1)
