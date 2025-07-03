from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Contenido, HistorialReproduccion, Calificacion, Favorito, Categoria
import random


class SistemaRecomendaciones:
    """
    Sistema de recomendaciones basado en:
    1. Historial de reproducción del usuario
    2. Calificaciones (likes/dislikes) del usuario
    3. Contenido similar por categorías
    4. Popularidad global
    5. Contenido reciente
    """
    
    def __init__(self, perfil):
        self.perfil = perfil
        
    def obtener_recomendaciones(self, limite=10):
        """
        Obtiene recomendaciones personalizadas para el usuario
        """
        recomendaciones = []
        
        # 1. Recomendaciones basadas en historial (40% del peso)
        recomendaciones_historial = self._recomendaciones_por_historial(limite//2)
        recomendaciones.extend(recomendaciones_historial)
        
        # 2. Recomendaciones basadas en calificaciones (30% del peso)
        recomendaciones_rating = self._recomendaciones_por_rating(limite//3)
        recomendaciones.extend(recomendaciones_rating)
        
        # 3. Recomendaciones basadas en categorías favoritas (20% del peso)
        recomendaciones_categorias = self._recomendaciones_por_categorias(limite//4)
        recomendaciones.extend(recomendaciones_categorias)
        
        # 4. Contenido popular y nuevo (10% del peso)
        recomendaciones_populares = self._recomendaciones_populares(limite//5)
        recomendaciones.extend(recomendaciones_populares)
        
        # Eliminar duplicados y contenido ya visto/calificado
        recomendaciones_unicas = self._filtrar_contenido_ya_visto(recomendaciones)
        
        # Si no hay suficientes recomendaciones, añadir contenido aleatorio
        if len(recomendaciones_unicas) < limite:
            contenido_restante = limite - len(recomendaciones_unicas)
            contenido_aleatorio = Contenido.objects.exclude(
                id__in=self._obtener_contenido_ya_visto()
            ).exclude(
                id__in=[r.id for r in recomendaciones_unicas]
            ).order_by('?')[:contenido_restante]
            
            recomendaciones_unicas.extend(list(contenido_aleatorio))
        
        # Mezclar y limitar
        random.shuffle(recomendaciones_unicas)
        return recomendaciones_unicas[:limite]
    
    def _recomendaciones_por_historial(self, limite):
        """
        Recomienda contenido similar al que ha reproducido el usuario
        """
        # Obtener categorías de contenido más reproducido
        categorias_vistas = Categoria.objects.filter(
            contenidos__historialreproduccion__perfil=self.perfil
        ).annotate(
            veces_visto=Count('contenidos__historialreproduccion')
        ).order_by('-veces_visto')[:8]  # Aumentado de 5 a 8
        
        if not categorias_vistas:
            # Fallback: usar categorías de contenido favorito
            categorias_vistas = Categoria.objects.filter(
                contenidos__favorito__perfil=self.perfil
            ).distinct()[:8]
            
        if not categorias_vistas:
            return []
            
        # Buscar contenido similar en esas categorías
        contenido_similar = Contenido.objects.filter(
            categorias__in=categorias_vistas
        ).exclude(
            id__in=self._obtener_contenido_ya_visto()
        ).distinct().order_by('?')[:limite]
        
        return list(contenido_similar)
    
    def _recomendaciones_por_rating(self, limite):
        """
        Recomienda contenido basado en las calificaciones positivas del usuario
        """
        # Obtener categorías de contenido con rating medio-alto (3-5 estrellas)
        categorias_gustadas = Categoria.objects.filter(
            contenidos__calificacion__perfil=self.perfil,
            contenidos__calificacion__calificacion__gte=3  # Reducido de 4 a 3
        ).annotate(
            promedio_rating=Avg('contenidos__calificacion__calificacion')
        ).order_by('-promedio_rating')[:8]  # Aumentado de 5 a 8
        
        if not categorias_gustadas:
            # Fallback: obtener categorías de cualquier contenido calificado
            categorias_gustadas = Categoria.objects.filter(
                contenidos__calificacion__perfil=self.perfil
            ).distinct()[:8]
        
        if not categorias_gustadas:
            return []
            
        # Buscar contenido en esas categorías con calificaciones globales decentes
        contenido_recomendado = Contenido.objects.filter(
            categorias__in=categorias_gustadas
        ).annotate(
            promedio_global=Avg('calificacion__calificacion'),
            total_ratings=Count('calificacion')
        ).filter(
            # Relajado: permitir contenido sin calificaciones O con rating >= 2.5
            Q(promedio_global__isnull=True) | Q(promedio_global__gte=2.5)
        ).exclude(
            id__in=self._obtener_contenido_ya_visto()
        ).distinct().order_by('-promedio_global', '-total_ratings', '?')[:limite]
        
        return list(contenido_recomendado)
    
    def _recomendaciones_por_categorias(self, limite):
        """
        Recomienda contenido de las categorías más frecuentes del usuario
        """
        # Obtener las categorías más frecuentes en el historial del usuario
        categorias_frecuentes = Categoria.objects.filter(
            Q(contenidos__historialreproduccion__perfil=self.perfil) |
            Q(contenidos__favorito__perfil=self.perfil)
        ).annotate(
            frecuencia=Count('contenidos__historialreproduccion') + Count('contenidos__favorito')
        ).order_by('-frecuencia')[:3]
        
        if not categorias_frecuentes:
            return []
            
        # Buscar contenido nuevo en esas categorías
        contenido_categorias = Contenido.objects.filter(
            categorias__in=categorias_frecuentes
        ).exclude(
            id__in=self._obtener_contenido_ya_visto()
        ).distinct().order_by('-año', '?')[:limite]
        
        return list(contenido_categorias)
    
    def _recomendaciones_populares(self, limite):
        """
        Recomienda contenido popular y reciente
        """
        # Contenido más reproducido globalmente en los últimos 90 días (aumentado de 30)
        fecha_limite = timezone.now() - timedelta(days=90)
        
        contenido_popular = Contenido.objects.annotate(
            reproducciones_recientes=Count(
                'historialreproduccion',
                filter=Q(historialreproduccion__fecha__gte=fecha_limite)
            ),
            reproducciones_totales=Count('historialreproduccion'),  # Agregado
            rating_promedio=Avg('calificacion__calificacion')
        ).filter(
            # Relajado: permitir contenido con reproducciones totales > 0 O recientes > 0
            Q(reproducciones_recientes__gt=0) | Q(reproducciones_totales__gt=0)
        ).exclude(
            id__in=self._obtener_contenido_ya_visto()
        ).order_by('-reproducciones_recientes', '-reproducciones_totales', '-rating_promedio', '?')[:limite]
        
        # Si no hay suficiente contenido popular, añadir contenido aleatorio reciente
        if len(contenido_popular) < limite:
            contenido_restante = limite - len(contenido_popular)
            contenido_extra = Contenido.objects.exclude(
                id__in=self._obtener_contenido_ya_visto()
            ).exclude(
                id__in=[c.id for c in contenido_popular]
            ).order_by('-id', '?')[:contenido_restante]
            
            contenido_popular = list(contenido_popular) + list(contenido_extra)
        
        return list(contenido_popular)
    
    def _obtener_contenido_ya_visto(self):
        """
        Obtiene IDs del contenido que ya ha visto/calificado el usuario
        """
        contenido_visto = set()
        
        # Contenido del historial
        historial_ids = HistorialReproduccion.objects.filter(
            perfil=self.perfil
        ).values_list('contenido_id', flat=True)
        contenido_visto.update(historial_ids)
          # Contenido calificado
        calificado_ids = Calificacion.objects.filter(
            perfil=self.perfil
        ).values_list('contenido_id', flat=True)
        contenido_visto.update(calificado_ids)
        
        # Favoritos
        favoritos_ids = Favorito.objects.filter(
            perfil=self.perfil
        ).values_list('contenido_id', flat=True)
        contenido_visto.update(favoritos_ids)
        
        return list(contenido_visto)
    
    def _filtrar_contenido_ya_visto(self, recomendaciones):
        """
        Filtra el contenido que el usuario ya ha visto
        """
        contenido_visto = set(self._obtener_contenido_ya_visto())
        return [contenido for contenido in recomendaciones if contenido.id not in contenido_visto]
    
    def obtener_recomendaciones_por_categoria(self, categoria, limite=8):
        """
        Obtiene recomendaciones específicas de una categoría
        """        # Obtener preferencias del usuario en esta categoría
        rating_usuario_categoria = Calificacion.objects.filter(
            perfil=self.perfil,
            contenido__categorias=categoria
        ).aggregate(promedio=Avg('calificacion'))['promedio'] or 3
        
        # Recomendar contenido de la categoría con buen rating
        contenido_categoria = Contenido.objects.filter(
            categorias=categoria
        ).annotate(
            rating_promedio=Avg('calificacion__calificacion'),
            total_ratings=Count('calificacion')
        ).exclude(
            id__in=self._obtener_contenido_ya_visto()        ).order_by('-rating_promedio', '-total_ratings', '?')[:limite]
        
        return list(contenido_categoria)

    def obtener_contenido_similar(self, contenido, limite=6):
        """
        Obtiene contenido similar a uno específico
        """
        # Buscar contenido con categorías similares
        categorias_contenido = contenido.categorias.all()
        
        if not categorias_contenido.exists():
            # Si no tiene categorías, devolver contenido popular
            return list(Contenido.objects.annotate(
                rating_promedio=Avg('calificacion__calificacion')
            ).exclude(id=contenido.id).order_by('-rating_promedio', '?')[:limite])
        
        contenido_similar = Contenido.objects.filter(
            categorias__in=categorias_contenido
        ).exclude(
            id=contenido.id
        ).exclude(
            id__in=self._obtener_contenido_ya_visto()
        ).annotate(
            categorias_compartidas=Count('categorias', filter=Q(categorias__in=categorias_contenido)),
            rating_promedio=Avg('calificacion__calificacion')
        ).order_by('-categorias_compartidas', '-rating_promedio', '?')[:limite]
        
        # Convertir a lista y verificar que todos los objetos tengan ID válido
        resultado = []
        for item in contenido_similar:
            if item and item.id:
                resultado.append(item)
        
        return resultado


def obtener_recomendaciones_para_perfil(perfil, limite=10):
    """
    Función helper para obtener recomendaciones para un perfil
    """
    sistema = SistemaRecomendaciones(perfil)
    return sistema.obtener_recomendaciones(limite)


def obtener_recomendaciones_por_categoria(perfil, categoria, limite=8):
    """
    Función helper para obtener recomendaciones por categoría
    """
    sistema = SistemaRecomendaciones(perfil)
    return sistema.obtener_recomendaciones_por_categoria(categoria, limite)


def obtener_contenido_similar(perfil, contenido, limite=6):
    """
    Función helper para obtener contenido similar
    """
    sistema = SistemaRecomendaciones(perfil)
    return sistema.obtener_contenido_similar(contenido, limite)