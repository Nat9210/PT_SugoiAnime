from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from .models import AuditLog, SesionUsuario, AccesoFallido
import csv
from django.contrib.auth.models import User

@staff_member_required
def audit_dashboard(request):
    """Panel de control de auditoría"""
    # Estadísticas generales
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    stats = {
        'total_logs': AuditLog.objects.count(),
        'logs_24h': AuditLog.objects.filter(timestamp__gte=last_24h).count(),
        'logs_7d': AuditLog.objects.filter(timestamp__gte=last_7d).count(),
        'logs_30d': AuditLog.objects.filter(timestamp__gte=last_30d).count(),
        'active_sessions': SesionUsuario.objects.filter(activa=True).count(),
        'failed_logins_24h': AccesoFallido.objects.filter(timestamp__gte=last_24h).count(),
        'unique_users_24h': AuditLog.objects.filter(
            timestamp__gte=last_24h, 
            usuario__isnull=False
        ).values('usuario').distinct().count(),
    }
    
    # Acciones más frecuentes en los últimos 7 días
    top_actions = AuditLog.objects.filter(
        timestamp__gte=last_7d
    ).values('accion').annotate(
        count=Count('accion')
    ).order_by('-count')[:10]
    
    # Usuarios más activos en los últimos 7 días
    top_users = AuditLog.objects.filter(
        timestamp__gte=last_7d,
        usuario__isnull=False
    ).values(
        'usuario__username'
    ).annotate(
        count=Count('usuario')
    ).order_by('-count')[:10]
    
    # Logs recientes con nivel de error o crítico
    error_logs = AuditLog.objects.filter(
        nivel__in=['ERROR', 'CRITICAL']
    ).order_by('-timestamp')[:20]
    
    # IPs con más intentos fallidos
    failed_ips = AccesoFallido.objects.filter(
        timestamp__gte=last_24h
    ).values('ip_address').annotate(
        count=Count('ip_address')
    ).order_by('-count')[:10]
    
    context = {
        'stats': stats,
        'top_actions': top_actions,
        'top_users': top_users,
        'error_logs': error_logs,
        'failed_ips': failed_ips,
    }
    
    return render(request, 'admin/audit_dashboard.html', context)

@staff_member_required
def audit_logs_view(request):
    """Vista de logs de auditoría con filtros"""
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    # Filtros
    accion = request.GET.get('accion')
    nivel = request.GET.get('nivel')
    usuario = request.GET.get('usuario')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if accion:
        logs = logs.filter(accion=accion)
    if nivel:
        logs = logs.filter(nivel=nivel)
    if usuario:
        logs = logs.filter(usuario__username__icontains=usuario)
    if fecha_desde:
        logs = logs.filter(timestamp__date__gte=fecha_desde)
    if fecha_hasta:
        logs = logs.filter(timestamp__date__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Opciones para filtros
    acciones = AuditLog.ACCION_CHOICES
    niveles = AuditLog.NIVEL_CHOICES
    
    context = {
        'page_obj': page_obj,
        'acciones': acciones,
        'niveles': niveles,
        'filters': {
            'accion': accion,
            'nivel': nivel,
            'usuario': usuario,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }
    
    return render(request, 'admin/audit_logs.html', context)

@staff_member_required
def session_monitoring(request):
    """Monitoreo de sesiones activas"""
    active_sessions = SesionUsuario.objects.filter(activa=True).order_by('-fecha_inicio')
    recent_sessions = SesionUsuario.objects.filter(activa=False).order_by('-fecha_fin')[:20]
    
    context = {
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'admin/session_monitoring.html', context)

@staff_member_required
def security_alerts(request):
    """Alertas de seguridad"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    # Múltiples intentos fallidos desde la misma IP
    suspicious_ips = AccesoFallido.objects.filter(
        timestamp__gte=last_24h
    ).values('ip_address').annotate(
        count=Count('ip_address')
    ).filter(count__gte=5).order_by('-count')
    
    # Accesos desde IPs inusuales
    # (IPs que nunca antes habían accedido exitosamente)
    failed_ips = set(AccesoFallido.objects.filter(
        timestamp__gte=last_24h
    ).values_list('ip_address', flat=True))
    
    successful_ips = set(AuditLog.objects.filter(
        accion='LOGIN',
        nivel='INFO'
    ).values_list('ip_address', flat=True))
    
    new_ips = failed_ips - successful_ips
    
    # Múltiples sesiones activas para el mismo usuario
    multi_sessions = SesionUsuario.objects.filter(
        activa=True
    ).values('usuario').annotate(
        count=Count('usuario')
    ).filter(count__gt=1)
    
    context = {
        'suspicious_ips': suspicious_ips,
        'new_ips': new_ips,
        'multi_sessions': multi_sessions,
    }
    
    return render(request, 'admin/security_alerts.html', context)

@staff_member_required
def export_audit_logs(request):
    """Exportar logs de auditoría a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Timestamp', 'Usuario', 'Perfil', 'Acción', 'Descripción', 
        'Nivel', 'IP Address', 'User Agent', 'Tabla Afectada', 'Objeto ID'
    ])
    
    # Aplicar los mismos filtros que en la vista de logs
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    accion = request.GET.get('accion')
    nivel = request.GET.get('nivel')
    usuario = request.GET.get('usuario')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if accion:
        logs = logs.filter(accion=accion)
    if nivel:
        logs = logs.filter(nivel=nivel)
    if usuario:
        logs = logs.filter(usuario__username__icontains=usuario)
    if fecha_desde:
        logs = logs.filter(timestamp__date__gte=fecha_desde)
    if fecha_hasta:
        logs = logs.filter(timestamp__date__lte=fecha_hasta)
    
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.usuario.username if log.usuario else '',
            log.perfil.nombre if log.perfil else '',
            log.get_accion_display(),
            log.descripcion,
            log.get_nivel_display(),
            log.ip_address or '',
            log.user_agent,
            log.tabla_afectada,
            log.objeto_id,
        ])
    
    return response

@staff_member_required
def audit_stats_api(request):
    """API para estadísticas de auditoría (para gráficos)"""
    days = int(request.GET.get('days', 7))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Logs por día
    logs_by_day = {}
    for i in range(days):
        date = (start_date + timedelta(days=i)).date()
        count = AuditLog.objects.filter(timestamp__date=date).count()
        logs_by_day[date.strftime('%Y-%m-%d')] = count
    
    # Logs por acción
    logs_by_action = {}
    for accion, nombre in AuditLog.ACCION_CHOICES:
        count = AuditLog.objects.filter(
            accion=accion,
            timestamp__gte=start_date
        ).count()
        logs_by_action[nombre] = count
    
    # Logs por nivel
    logs_by_level = {}
    for nivel, nombre in AuditLog.NIVEL_CHOICES:
        count = AuditLog.objects.filter(
            nivel=nivel,
            timestamp__gte=start_date
        ).count()
        logs_by_level[nombre] = count
    
    return JsonResponse({
        'logs_by_day': logs_by_day,
        'logs_by_action': logs_by_action,
        'logs_by_level': logs_by_level,
    })
