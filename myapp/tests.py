from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import override_settings
from .models import Contenido, Categoria, Episodio, Perfil, ContenidoCategoria
import time
from django.core.cache import cache
from django.test import TransactionTestCase
from django.db import connections
from threading import Thread
import concurrent.futures


class ModeloTestCase(TestCase):
    """Pruebas unitarias para modelos"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.categoria = Categoria.objects.create(nombre='Acción')
        self.contenido = Contenido.objects.create(
            titulo='Test Anime',
            tipo='serie',
            descripcion='Un anime de prueba',
            año=2024,
            duracion=24
        )
        
    def test_crear_contenido(self):
        """Probar creación de contenido"""
        self.assertEqual(self.contenido.titulo, 'Test Anime')
        self.assertEqual(self.contenido.tipo, 'serie')
        self.assertEqual(self.contenido.año, 2024)
        
    def test_relacion_categoria(self):
        """Probar relación many-to-many con categorías"""
        ContenidoCategoria.objects.create(contenido=self.contenido, categoria=self.categoria)
        self.assertIn(self.categoria, self.contenido.categorias.all())
        
    def test_crear_episodio(self):
        """Probar creación de episodios"""
        episodio = Episodio.objects.create(
            serie=self.contenido,
            temporada=1,
            numero_episodio=1,
            titulo='Episodio 1',
            duracion=24,
            video_url='https://example.com/video1.mp4'
        )
        self.assertEqual(episodio.serie, self.contenido)
        self.assertEqual(episodio.temporada, 1)


class BusquedaTestCase(TestCase):
    """Pruebas para funcionalidad de búsqueda"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Crear contenido de prueba
        self.categoria_accion = Categoria.objects.create(nombre='Acción')
        self.categoria_drama = Categoria.objects.create(nombre='Drama')
        
        self.anime1 = Contenido.objects.create(
            titulo='Naruto',
            tipo='serie',
            año=2002,
            descripcion='Ninja adventures'
        )
        self.anime2 = Contenido.objects.create(
            titulo='One Piece',
            tipo='serie',
            año=1999,
            descripcion='Pirate adventures'
        )
        self.pelicula1 = Contenido.objects.create(
            titulo='Your Name',
            tipo='pelicula',
            año=2016,
            descripcion='Romance drama'
        )
        
        # Asociar categorías
        ContenidoCategoria.objects.create(contenido=self.anime1, categoria=self.categoria_accion)
        ContenidoCategoria.objects.create(contenido=self.pelicula1, categoria=self.categoria_drama)
        
    def test_busqueda_por_titulo(self):
        """Probar búsqueda por título"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('busqueda'), {'q': 'Naruto'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Naruto')
        self.assertNotContains(response, 'One Piece')
        
    def test_busqueda_por_tipo(self):
        """Probar búsqueda por tipo"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('busqueda'), {'q': 'serie'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Naruto')
        self.assertContains(response, 'One Piece')
        self.assertNotContains(response, 'Your Name')
        
    def test_busqueda_por_categoria(self):
        """Probar búsqueda por categoría"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('busqueda'), {'q': 'Acción'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Naruto')
        
    def test_busqueda_vacia(self):
        """Probar búsqueda vacía"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('busqueda'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Naruto')


class RendimientoTestCase(TestCase):
    """Pruebas de rendimiento y carga"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Crear datos masivos para pruebas de carga
        categorias = []
        for i in range(10):
            categoria = Categoria.objects.create(nombre=f'Categoria{i}')
            categorias.append(categoria)
            
        # Crear 100 contenidos para simular carga
        contenidos = []
        for i in range(100):
            contenido = Contenido.objects.create(
                titulo=f'Anime {i}',
                tipo='serie' if i % 2 == 0 else 'pelicula',
                año=2000 + (i % 25),
                descripcion=f'Descripción del anime {i} con palabras clave especiales',
                duracion=24
            )
            contenidos.append(contenido)
            
            # Asociar categorías aleatoriamente
            categoria = categorias[i % len(categorias)]
            ContenidoCategoria.objects.create(contenido=contenido, categoria=categoria)
            
    def test_rendimiento_index(self):
        """Probar rendimiento de página principal"""
        self.client.login(username='testuser', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('index'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        load_time = end_time - start_time
        self.assertLess(load_time, 2.0, f"Página principal tomó {load_time:.2f}s, debe ser < 2s")
        
    def test_rendimiento_busqueda(self):
        """Probar rendimiento de búsqueda"""
        self.client.login(username='testuser', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('busqueda'), {'q': 'Anime'})
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        load_time = end_time - start_time
        self.assertLess(load_time, 1.0, f"Búsqueda tomó {load_time:.2f}s, debe ser < 1s")
        
    def test_rendimiento_categorias(self):
        """Probar rendimiento de página de categorías"""
        self.client.login(username='testuser', password='testpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('categories'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        load_time = end_time - start_time
        self.assertLess(load_time, 1.5, f"Categorías tomó {load_time:.2f}s, debe ser < 1.5s")
        
    def test_consultas_db_optimizadas(self):
        """Probar que las consultas están optimizadas"""
        self.client.login(username='testuser', password='testpass123')
        
        with self.assertNumQueries(5):  # Máximo 5 consultas SQL
            response = self.client.get(reverse('index'))
            self.assertEqual(response.status_code, 200)


class CargaConcurrenteTestCase(TransactionTestCase):
    """Pruebas de carga concurrente"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Crear contenido para las pruebas
        for i in range(50):
            Contenido.objects.create(
                titulo=f'Test Anime {i}',
                tipo='serie',
                año=2020,
                duracion=24
            )
    
    def test_carga_concurrente_busqueda(self):
        """Probar búsquedas concurrentes"""
        def realizar_busqueda():
            client = Client()
            client.login(username='testuser', password='testpass123')
            response = client.get(reverse('busqueda'), {'q': 'Test'})
            return response.status_code == 200
            
        # Simular 10 usuarios simultáneos
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(realizar_busqueda) for _ in range(10)]
            resultados = [future.result() for future in futures]
            
        # Todos deben tener éxito
        self.assertTrue(all(resultados), "Algunas búsquedas concurrentes fallaron")
        
    def test_carga_concurrente_index(self):
        """Probar carga concurrente en página principal"""
        def acceder_index():
            client = Client()
            client.login(username='testuser', password='testpass123')
            start = time.time()
            response = client.get(reverse('index'))
            end = time.time()
            return response.status_code == 200 and (end - start) < 3.0
            
        # Simular 20 usuarios simultáneos
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(acceder_index) for _ in range(20)]
            resultados = [future.result() for future in futures]
            
        success_rate = sum(resultados) / len(resultados)
        self.assertGreater(success_rate, 0.8, f"Tasa de éxito: {success_rate:.2%}, debe ser > 80%")


class IntegracionTestCase(TestCase):
    """Pruebas de integración completas"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.perfil = Perfil.objects.create(usuario=self.user, nombre='Test User', tipo='adulto')
        
    def test_flujo_completo_usuario(self):
        """Probar flujo completo: login -> buscar -> ver detalles"""
        # 1. Login
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)
        
        # 2. Crear contenido
        contenido = Contenido.objects.create(
            titulo='Test Integration Anime',
            tipo='serie',
            año=2024,
            descripcion='Anime para pruebas de integración'
        )
        
        # 3. Acceder a página principal
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        
        # 4. Realizar búsqueda
        response = self.client.get(reverse('busqueda'), {'q': 'Integration'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Integration Anime')
        
        # 5. Ver detalles
        response = self.client.get(reverse('anime_details', args=[contenido.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Integration Anime')


# Create your tests here.
