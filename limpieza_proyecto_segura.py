#!/usr/bin/env python3
"""
Script de limpieza segura para SugoiAnime
Elimina archivos innecesarios, duplicados y obsoletos
Crea un respaldo antes de eliminar
"""

import os
import shutil
from datetime import datetime
import json

def crear_respaldo_seguridad():
    """Crea un directorio de respaldo con los archivos que se van a eliminar"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"respaldo_limpieza_{timestamp}"
    
    print(f"🔄 Creando directorio de respaldo: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    
    return backup_dir

def eliminar_archivo_seguro(archivo, backup_dir):
    """Elimina un archivo de forma segura, creando respaldo primero"""
    if os.path.exists(archivo):
        # Crear respaldo
        backup_path = os.path.join(backup_dir, os.path.basename(archivo))
        try:
            if os.path.isfile(archivo):
                shutil.copy2(archivo, backup_path)
                os.remove(archivo)
                print(f"✅ Eliminado: {archivo}")
                return True
            elif os.path.isdir(archivo):
                shutil.copytree(archivo, backup_path)
                shutil.rmtree(archivo)
                print(f"✅ Eliminado directorio: {archivo}")
                return True
        except Exception as e:
            print(f"❌ Error al eliminar {archivo}: {e}")
            return False
    else:
        print(f"⚠️  Archivo no encontrado: {archivo}")
        return False

def limpiar_proyecto():
    """Función principal de limpieza"""
    
    print("🧹 LIMPIEZA SEGURA DEL PROYECTO SUGOIANIME")
    print("=" * 50)
    
    # Crear respaldo
    backup_dir = crear_respaldo_seguridad()
    
    # Lista de archivos a eliminar
    archivos_eliminar = [
        # Archivos de prueba vacíos y obsoletos
        "test_stats_final.py",
        "test_stats_final_fixed.py", 
        "test_anilist.py",
        "test_anilist_español.py",
        "test_simple_anilist.py",
        "test_complete_stats.py",
        "test_audit_system.py",
        "test_busqueda_script.py",
        "test_historial_busqueda.py",
        "test_email_simple.py",
        "test_http_request.py",
        "test_password_reset_console.py",
        "test_password_reset_system.py",
        "test_visual_reset.py",
        
        # Scripts temporales de desarrollo
        "verificar_estado.py",
        "validar_index_dinamico.py",
        "ejecutar_en_shell.py",
        "validate_audit_system.py",
        "generar_esquema_simple.py",
        "generar_esquema_sql.py",
        "limpiar_proyecto.py",
        
        # Documentación duplicada y vacía
        "GUIA_VIDEOS_S3.md",
        "GUIA_VIDEOS_S3 copy.md",
        "REPORTE_LOGO_HEADER_FIJO.md",
        "ELIMINACION_ETIQUETA_CARGA.md",
        "REPORTE_CAMBIOS_BADGE.md",
        "REPORTE_CAMBIOS_CARGA_VIDEO.md",
        "REPORTE_SPRINT2_COMPLETITUD.md",
        "REPORTE_SPRINT3_ANALISIS_RATING.md",
        
        # Archivos de configuración obsoletos
        "dbdiagram_schema.txt",
        "sugoianime_schema_fixed.sql",
        
        # Archivos temporales y de respaldo
        "backup_data.json",
        "desktop.ini",
        
        # Documentación obsoleta
        "CAMBIOS_SISTEMA_VIDEOS.md",
        "SOLUCION_YOUTUBE.md", 
        "INSTALACION_GITHUB.md",
        "INSTRUCCIONES_DIAGRAMA.md",
          # Carpetas generadas
        "staticfiles"
    ]
    
    eliminados_exitosos = 0
    errores = 0
    
    print(f"\n📋 Archivos programados para eliminación: {len(archivos_eliminar)}")
    print("\n🗑️  Iniciando eliminación...\n")
    
    for archivo in archivos_eliminar:
        if eliminar_archivo_seguro(archivo, backup_dir):
            eliminados_exitosos += 1
        else:
            errores += 1
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE LIMPIEZA")
    print("=" * 50)
    print(f"✅ Archivos eliminados exitosamente: {eliminados_exitosos}")
    print(f"❌ Errores encontrados: {errores}")
    print(f"💾 Respaldo creado en: {backup_dir}")
    
    # Crear log de la limpieza
    log_limpieza = {
        "fecha": datetime.now().isoformat(),
        "archivos_eliminados": eliminados_exitosos,
        "errores": errores,
        "directorio_respaldo": backup_dir,
        "archivos_procesados": archivos_eliminar
    }
    
    with open(os.path.join(backup_dir, "log_limpieza.json"), "w", encoding="utf-8") as f:
        json.dump(log_limpieza, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Log de limpieza guardado en: {backup_dir}/log_limpieza.json")
    
    if eliminados_exitosos > 0:
        print("\n🎉 ¡Limpieza completada exitosamente!")
        print("🔍 Si necesitas recuperar algún archivo, revisa el directorio de respaldo.")
    else:
        print("\n⚠️  No se eliminaron archivos. Revisa los errores.")
    
    return eliminados_exitosos, errores

if __name__ == "__main__":
    try:
        limpiar_proyecto()
    except KeyboardInterrupt:
        print("\n⚠️  Limpieza cancelada por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
