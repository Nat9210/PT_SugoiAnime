from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Perfil, Contenido, Categoria, Calificacion, HistorialReproduccion, Favorito
import random
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema de recomendaciones'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Número de usuarios de prueba a crear')
        parser.add_argument('--interactions', type=int, default=20, help='Número de interacciones por usuario')

    def handle(self, *args, **options):
        num_users = options['users']
        num_interactions = options['interactions']
        
        self.stdout.write('Generando datos de prueba para el sistema de recomendaciones...')
        
        # Obtener o crear categorías si no existen
        categorias = ['Acción', 'Drama', 'Comedia', 'Romance', 'Thriller', 'Sci-Fi', 'Fantasy', 'Horror']
        categoria_objects = []
        for cat_name in categorias:
            categoria, created = Categoria.objects.get_or_create(nombre=cat_name)
            categoria_objects.append(categoria)
            if created:
                self.stdout.write(f'Categoría creada: {cat_name}')
        
        # Crear usuarios de prueba si no existen
        users_created = 0
        for i in range(num_users):
            username = f'usuario_test_{i+1}'
            email = f'test{i+1}@example.com'
            
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Usuario',
                    'last_name': f'Test {i+1}',
                }
            )
            
            if user_created:
                user.set_password('testpass123')
                user.save()
                users_created += 1
                
                # Crear perfil
                perfil, perfil_created = Perfil.objects.get_or_create(
                    usuario=user,
                    defaults={
                        'nombre': f'Perfil Test {i+1}',
                        'tipo': 'adulto'
                    }
                )
                
                self.stdout.write(f'Usuario creado: {username}')
                
                # Generar interacciones aleatorias
                contenidos = list(Contenido.objects.all())
                if contenidos:
                    for _ in range(num_interactions):
                        contenido = random.choice(contenidos)
                        
                        # Probabilidad de interacción
                        action = random.choice(['historial', 'rating', 'favorito', 'skip'])
                        
                        if action == 'historial':
                            # Crear entrada en historial
                            HistorialReproduccion.objects.get_or_create(
                                perfil=perfil,
                                contenido=contenido,
                                defaults={
                                    'tiempo_reproducido': random.randint(300, 7200),  # 5min a 2h
                                    'fecha': timezone.now() - timedelta(days=random.randint(1, 30))
                                }
                            )
                        elif action == 'rating':
                            # Crear calificación
                            calificacion = random.choice([1, 2, 3, 4, 5])
                            Calificacion.objects.get_or_create(
                                perfil=perfil,
                                contenido=contenido,
                                defaults={
                                    'calificacion': calificacion,
                                    'fecha': timezone.now() - timedelta(days=random.randint(1, 30))
                                }
                            )
                            
                        elif action == 'favorito':
                            # Añadir a favoritos
                            Favorito.objects.get_or_create(
                                perfil=perfil,
                                contenido=contenido,
                                defaults={
                                    'fecha_agregado': timezone.now() - timedelta(days=random.randint(1, 30))
                                }
                            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'¡Datos de prueba generados exitosamente!\n'
                f'- Usuarios creados: {users_created}\n'
                f'- Categorías disponibles: {len(categoria_objects)}\n'
                f'- Contenido disponible: {Contenido.objects.count()}\n'
                f'- Total de interacciones generadas: {HistorialReproduccion.objects.count() + Calificacion.objects.count() + Favorito.objects.count()}'
            )
        )
        
        self.stdout.write(
            'Para probar el sistema de recomendaciones:\n'
            '1. Inicia sesión con cualquiera de los usuarios test (password: testpass123)\n'
            '2. Ve a la página principal para ver recomendaciones personalizadas\n'
            '3. Ve a /recomendaciones/ para ver todas las recomendaciones\n'
            '4. Visita los detalles de cualquier contenido para ver contenido similar'
        )
