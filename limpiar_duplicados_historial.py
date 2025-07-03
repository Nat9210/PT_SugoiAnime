import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sugoianime.settings')
django.setup()

from myapp.models import HistorialReproduccion
from django.db.models import Count

def limpiar_duplicados_historial():
    """Limpia registros duplicados de HistorialReproduccion"""
    
    print("Iniciando limpieza de registros duplicados en HistorialReproduccion...")
    
    # Encontrar duplicados agrupando por perfil, contenido y episodio
    duplicados = HistorialReproduccion.objects.values(
        'perfil', 'contenido', 'episodio'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    total_duplicados = duplicados.count()
    print(f"Encontrados {total_duplicados} grupos de registros duplicados")
    
    registros_eliminados = 0
    
    for dup in duplicados:
        # Obtener todos los registros duplicados para este grupo
        registros = HistorialReproduccion.objects.filter(
            perfil=dup['perfil'],
            contenido=dup['contenido'],
            episodio=dup['episodio']
        ).order_by('fecha')  # Ordenar por fecha para mantener el más antiguo
        
        # Mantener solo el primer registro (más antiguo) y eliminar el resto
        registros_a_eliminar = registros[1:]  # Todos excepto el primero
        count_eliminados = len(registros_a_eliminar)
        
        if count_eliminados > 0:
            perfil_nombre = registros.first().perfil.nombre if registros.first().perfil else "Sin perfil"
            contenido_titulo = registros.first().contenido.titulo if registros.first().contenido else "Sin contenido"
            episodio_info = f"Episodio {registros.first().episodio.numero_episodio}" if registros.first().episodio else "Película"
            
            print(f"  - Eliminando {count_eliminados} duplicados para: {perfil_nombre} - {contenido_titulo} - {episodio_info}")
            
            # Eliminar los duplicados
            for registro in registros_a_eliminar:
                registro.delete()
                registros_eliminados += 1
    
    print(f"\nLimpieza completada:")
    print(f"  - Total de registros duplicados eliminados: {registros_eliminados}")
    print(f"  - Grupos de duplicados procesados: {total_duplicados}")
    
    # Verificar que no quedan duplicados
    duplicados_restantes = HistorialReproduccion.objects.values(
        'perfil', 'contenido', 'episodio'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1).count()
    
    print(f"  - Duplicados restantes: {duplicados_restantes}")
    
    if duplicados_restantes == 0:
        print("✅ Base de datos limpia, no hay duplicados restantes")
    else:
        print("⚠️  Aún quedan algunos duplicados")

if __name__ == "__main__":
    limpiar_duplicados_historial()
