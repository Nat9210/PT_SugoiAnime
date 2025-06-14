#!/usr/bin/env python3
"""
Script para limpiar archivos obsoletos del proyecto SugoiAnime
"""

import os
import shutil
from datetime import datetime

def limpiar_archivos_obsoletos():
    """Elimina archivos que ya no son necesarios"""
    
    print("🧹 LIMPIEZA DE ARCHIVOS OBSOLETOS")
    print("=" * 40)
    
    # Crear backup antes de eliminar
    backup_dir = f"backup_archivos_eliminados_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Lista de archivos a eliminar
    archivos_eliminar = [
        # Scripts de testing obsoletos
        'test_anilist.py',
        'test_anilist_español.py', 
        'test_simple_anilist.py',
        'test_stats_data.py',
        'test_stats_final.py',
        'test_audit_system.py',
        'test_busqueda_script.py',
        'test_complete_stats.py',
        'test_historial_busqueda.py',
        
        # Scripts temporales
        'create_test_data.py',
        'demo_anilist_español.py',
        'ejecutar_en_shell.py',
        'validar_index_dinamico.py',
        'verificar_estado.py',
        
        # Documentación obsoleta
        'REPORTE_LOGO_HEADER_FIJO.md',
        'ELIMINACION_ETIQUETA_CARGA.md',
        'REPORTE_CAMBIOS_BADGE.md',
        'ESTADO_FINAL_VALIDACION.md',
        
        # Esquemas con errores
        'sugoianime_schema.sql',
        'generar_esquema_sql.py',
        
        # Logs de desarrollo
        'django_errors.log',
        
        # Sistema
        'desktop.ini'
    ]
    
    # Logs específicos a eliminar
    logs_eliminar = [
        'logs/django_errors.log',
        'logs/django_general.log'
    ]
    
    eliminados = 0
    respaldados = 0
    
    # Eliminar archivos principales
    for archivo in archivos_eliminar:
        if os.path.exists(archivo):
            try:
                # Hacer backup primero
                backup_path = os.path.join(backup_dir, archivo)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(archivo, backup_path)
                respaldados += 1
                
                # Eliminar original
                os.remove(archivo)
                print(f"✅ Eliminado: {archivo}")
                eliminados += 1
            except Exception as e:
                print(f"❌ Error eliminando {archivo}: {e}")
        else:
            print(f"⚠️  No encontrado: {archivo}")
    
    # Eliminar logs específicos
    for log in logs_eliminar:
        if os.path.exists(log):
            try:
                backup_path = os.path.join(backup_dir, log)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(log, backup_path)
                respaldados += 1
                
                os.remove(log)
                print(f"✅ Eliminado log: {log}")
                eliminados += 1
            except Exception as e:
                print(f"❌ Error eliminando {log}: {e}")
    
    print(f"\n📊 RESUMEN:")
    print(f"   Archivos eliminados: {eliminados}")
    print(f"   Archivos respaldados: {respaldados}")
    print(f"   Backup creado en: {backup_dir}")
    
    # Mostrar estructura limpia
    print(f"\n📁 ARCHIVOS MANTENIDOS (importantes):")
    archivos_importantes = [
        'manage.py',
        'requirements.txt', 
        'db.sqlite3',
        'sugoianime_schema_fixed.sql',
        'dbdiagram_schema.txt',
        'mysql_setup.py',
        'README.md',
        'ANALISIS_TECNICO_COMPLETO.md'
    ]
    
    for archivo in archivos_importantes:
        if os.path.exists(archivo):
            print(f"   ✅ {archivo}")
    
    print(f"\n🎯 DIRECTORIOS PRINCIPALES INTACTOS:")
    directorios = ['myapp/', 'sugoianime/', 'media/', 'staticfiles/', 'venv/', '.git/']
    for directorio in directorios:
        if os.path.exists(directorio):
            print(f"   ✅ {directorio}")

def mostrar_recomendaciones():
    """Muestra recomendaciones adicionales"""
    print(f"\n💡 RECOMENDACIONES ADICIONALES:")
    print("   1. Revisar archivos en media/ y eliminar imágenes no usadas")
    print("   2. Limpiar cache de Django: python manage.py clearsessions")
    print("   3. Revisar logs/audit.log y mantener solo registros recientes")
    print("   4. Considerar comprimir backup_data.json si es muy grande")
    print("   5. Actualizar .gitignore para excluir archivos temporales futuros")

if __name__ == "__main__":
    respuesta = input("¿Proceder con la limpieza? (s/N): ")
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        limpiar_archivos_obsoletos()
        mostrar_recomendaciones()
        print("\n🎉 ¡Limpieza completada!")
    else:
        print("Operación cancelada.")
