from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Perfil, Contenido, Categoria, Calificacion, HistorialReproduccion, Favorito
from myapp.recommendations import obtener_recomendaciones_para_perfil
from django.db.models import Count, Avg
import csv
from datetime import datetime


class Command(BaseCommand):
    help = 'Genera un reporte completo del sistema de recomendaciones'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='reporte_recomendaciones.csv', help='Archivo de salida del reporte')
        parser.add_argument('--test-user', type=str, help='Username para probar recomendaciones específicas')

    def handle(self, *args, **options):
        output_file = options['output']
        test_user = options['test_user']
        
        self.stdout.write('🔄 Generando reporte del sistema de recomendaciones...')
        
        # Estadísticas generales
        stats = {
            'fecha_reporte': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_usuarios': User.objects.count(),
            'total_perfiles': Perfil.objects.count(),
            'total_contenido': Contenido.objects.count(),
            'total_categorias': Categoria.objects.count(),
            'total_reproducciones': HistorialReproduccion.objects.count(),            'total_calificaciones': Calificacion.objects.count(),
            'total_favoritos': Favorito.objects.count(),
        }
        
        # Análisis de calificaciones
        likes = Calificacion.objects.filter(calificacion__gte=4).count()
        dislikes = Calificacion.objects.filter(calificacion__lte=2).count()
        neutrales = Calificacion.objects.filter(calificacion=3).count()
        
        promedio_cal = Calificacion.objects.aggregate(Avg('calificacion'))['calificacion__avg']
        stats.update({
            'likes': likes,
            'dislikes': dislikes,
            'neutrales': neutrales,
            'promedio_calificacion': round(promedio_cal, 2) if promedio_cal else 0,
        })
        
        # Mostrar estadísticas en consola
        self.stdout.write(self.style.SUCCESS('\n📊 ESTADÍSTICAS GENERALES:'))
        for key, value in stats.items():
            self.stdout.write(f'  {key}: {value}')
          # Top usuarios más activos
        self.stdout.write(self.style.SUCCESS('\n👥 TOP 5 USUARIOS MÁS ACTIVOS:'))
        usuarios_activos = Perfil.objects.annotate(
            total_actividad=Count('historialreproduccion') + 
                           Count('calificacion') + 
                           Count('favorito')
        ).filter(total_actividad__gt=0).order_by('-total_actividad')[:5]
        
        if usuarios_activos:
            for perfil in usuarios_activos:
                self.stdout.write(f'  • {perfil.nombre}: {perfil.total_actividad} interacciones')
        else:
            self.stdout.write('  No hay usuarios activos')
          # Top contenido más popular
        self.stdout.write(self.style.SUCCESS('\n🎬 TOP 5 CONTENIDO MÁS POPULAR:'))
        contenido_popular = Contenido.objects.annotate(
            total_interacciones=Count('historialreproduccion') + 
                               Count('calificacion') + 
                               Count('favorito')
        ).filter(total_interacciones__gt=0).order_by('-total_interacciones')[:5]
        
        if contenido_popular:
            for contenido in contenido_popular:
                self.stdout.write(f'  • {contenido.titulo}: {contenido.total_interacciones} interacciones')
        else:
            self.stdout.write('  No hay contenido con interacciones')
        
        # Top categorías
        self.stdout.write(self.style.SUCCESS('\n🏷️ TOP 5 CATEGORÍAS MÁS POPULARES:'))
        categorias_populares = Categoria.objects.annotate(
            total_interacciones=Count('contenidos__historialreproduccion') + 
                               Count('contenidos__comentario') + 
                               Count('contenidos__favorito')
        ).filter(total_interacciones__gt=0).order_by('-total_interacciones')[:5]
        
        if categorias_populares:
            for categoria in categorias_populares:
                self.stdout.write(f'  • {categoria.nombre}: {categoria.total_interacciones} interacciones')
        else:
            self.stdout.write('  No hay categorías con interacciones')
        
        # Prueba de recomendaciones para usuario específico
        if test_user:
            self.stdout.write(self.style.SUCCESS(f'\n🎯 PRUEBA DE RECOMENDACIONES PARA: {test_user}'))
            try:
                user = User.objects.get(username=test_user)
                perfil = user.perfiles.first()
                if perfil:
                    recomendaciones = obtener_recomendaciones_para_perfil(perfil, limite=5)
                    self.stdout.write(f'  ✅ Recomendaciones generadas: {len(recomendaciones)}')
                    for i, contenido in enumerate(recomendaciones, 1):
                        self.stdout.write(f'    {i}. {contenido.titulo} ({contenido.get_tipo_display()})')
                else:
                    self.stdout.write('  ❌ Usuario no tiene perfil')
            except User.DoesNotExist:
                self.stdout.write('  ❌ Usuario no encontrado')
        
        # Estado del sistema
        total_interacciones = stats['total_reproducciones'] + stats['total_calificaciones'] + stats['total_favoritos']
        
        self.stdout.write(self.style.SUCCESS('\n✅ REPORTE COMPLETADO'))
        self.stdout.write(f'📈 Total de registros analizados: {total_interacciones}')
        
        # Estado del sistema
        if stats['total_contenido'] > 0 and total_interacciones > 0:
            estado = "🟢 SISTEMA ACTIVO Y FUNCIONAL"
        elif stats['total_contenido'] > 0:
            estado = "🟡 SISTEMA LISTO - NECESITA MÁS INTERACCIONES"
        else:
            estado = "🔴 SISTEMA INACTIVO - NECESITA CONTENIDO"
        
        self.stdout.write(f'🎯 {estado}')
        
        # Recomendaciones de mejora
        self.stdout.write(self.style.WARNING('\n💡 RECOMENDACIONES DE MEJORA:'))
        mejoras = []
        
        if stats['total_calificaciones'] < 50:
            mejoras.append('Incrementar engagement: pocos ratings de usuarios')
        if stats['total_reproducciones'] < 100:
            mejoras.append('Promover más reproducciones de contenido')
        if stats['total_contenido'] < 20:
            mejoras.append('Añadir más contenido para mejorar recomendaciones')
        if total_interacciones == 0:
            mejoras.append('Implementar estrategias para obtener feedback de usuarios')
        
        if mejoras:
            for mejora in mejoras:
                self.stdout.write(f'  • {mejora}')
        else:
            self.stdout.write('  ✅ Sistema funcionando óptimamente')
        
        self.stdout.write(self.style.SUCCESS('\n🚀 PARA PROBAR EL SISTEMA:'))
        self.stdout.write('  1. python manage.py runserver')
        self.stdout.write('  2. Visitar /recomendaciones/ (requiere login)')
        self.stdout.write('  3. Visitar /admin/estadisticas-recomendaciones/ (requiere admin)')
        self.stdout.write(f'  4. Login con usuarios test: usuario_test_1, usuario_test_2, usuario_test_3 (password: testpass123)')
