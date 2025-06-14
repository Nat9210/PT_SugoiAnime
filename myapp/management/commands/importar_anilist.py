"""
Comando de gestión para importar contenido desde AniList
"""
from django.core.management.base import BaseCommand, CommandError
from myapp.anilist_importer import anilist_importer
from myapp.models import Contenido

class Command(BaseCommand):
    help = 'Importa contenido de anime desde AniList'

    def add_arguments(self, parser):
        parser.add_argument(
            '--populares',
            type=int,
            default=0,
            help='Número de animes populares a importar'
        )
        parser.add_argument(
            '--temporada',
            type=int,
            default=0,
            help='Número de animes de la temporada actual a importar'
        )
        parser.add_argument(
            '--buscar',
            type=str,
            help='Término de búsqueda para importar animes específicos'
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=10,
            help='Cantidad máxima de resultados a importar en búsqueda'
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Listar contenido ya importado desde AniList'
        )

    def handle(self, *args, **options):
        if options['listar']:
            self.listar_contenido_anilist()
            return

        if options['populares']:
            self.importar_populares(options['populares'])

        if options['temporada']:
            self.importar_temporada(options['temporada'])

        if options['buscar']:
            self.buscar_e_importar(options['buscar'], options['cantidad'])

        if not any([options['populares'], options['temporada'], options['buscar']]):
            self.stdout.write(
                self.style.WARNING('Especifica al menos una opción de importación.')
            )
            self.stdout.write('Usa --help para ver las opciones disponibles.')

    def importar_populares(self, cantidad):
        """Importar anime populares"""
        self.stdout.write(f'Importando {cantidad} animes populares desde AniList...')
        
        try:
            contenidos = anilist_importer.importar_populares(cantidad)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Se importaron {len(contenidos)} animes populares exitosamente.'
                )
            )
            
            for contenido in contenidos:
                self.stdout.write(f'  • {contenido.titulo} ({contenido.año or "N/A"})')
                
        except Exception as e:
            raise CommandError(f'Error al importar populares: {e}')

    def importar_temporada(self, cantidad):
        """Importar anime de temporada actual"""
        self.stdout.write(f'Importando {cantidad} animes de la temporada actual desde AniList...')
        
        try:
            contenidos = anilist_importer.importar_temporada_actual(cantidad)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Se importaron {len(contenidos)} animes de temporada exitosamente.'
                )
            )
            
            for contenido in contenidos:
                self.stdout.write(f'  • {contenido.titulo} ({contenido.año or "N/A"})')
                
        except Exception as e:
            raise CommandError(f'Error al importar temporada: {e}')

    def buscar_e_importar(self, termino, cantidad):
        """Buscar e importar animes específicos"""
        self.stdout.write(f'Buscando "{termino}" en AniList (máximo {cantidad} resultados)...')
        
        try:
            contenidos = anilist_importer.buscar_e_importar(termino, cantidad)
            
            if contenidos:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Se importaron {len(contenidos)} animes para "{termino}".'
                    )
                )
                
                for contenido in contenidos:
                    self.stdout.write(f'  • {contenido.titulo} ({contenido.año or "N/A"})')
            else:
                self.stdout.write(
                    self.style.WARNING(f'❌ No se encontraron resultados para "{termino}".')
                )
                
        except Exception as e:
            raise CommandError(f'Error en búsqueda: {e}')

    def listar_contenido_anilist(self):
        """Listar contenido importado desde AniList"""
        contenidos = Contenido.objects.filter(anilist_id__isnull=False).order_by('-fecha_importacion')
        
        if not contenidos.exists():
            self.stdout.write(
                self.style.WARNING('No hay contenido importado desde AniList.')
            )
            return
        
        self.stdout.write(f'Contenido importado desde AniList ({contenidos.count()} total):')
        self.stdout.write('-' * 60)
        
        for contenido in contenidos:
            score = f" (Score: {contenido.anilist_score})" if contenido.anilist_score else ""
            popularity = f" (Popularidad: {contenido.anilist_popularity})" if contenido.anilist_popularity else ""
            
            self.stdout.write(
                f'• {contenido.titulo} ({contenido.año or "N/A"}) - ID: {contenido.anilist_id}{score}{popularity}'
            )
