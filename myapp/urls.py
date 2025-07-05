from django.urls import path
from . import views
from . import audit_views

urlpatterns = [
    # Rutas de la aplicación
    path('', views.index, name='home'),
    path('index/', views.index, name='index'),
    path('anime-details/', views.render_anime_details, name='anime_details'),
    path('anime-details/<int:contenido_id>/', views.anime_details, name='anime_details'),
    path('anime-watching/<int:episodio_id>/', views.anime_watching, name='anime_watching'),
    path('movie-watching/<int:contenido_id>/', views.movie_watching, name='movie_watching'),
    path('blog-details/', views.render_blog_details, name='blog_details'), #sin función
    path('blog/', views.render_blog, name='blog'), #sin función
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('categories/', views.render_categories, name='categories'),
    # CRUD Contenido
    path('contenido/', views.contenido_list, name='contenido_list'),
    path('contenido/crear/', views.contenido_create, name='contenido_create'),
    path('contenido/<int:pk>/editar/', views.contenido_update, name='contenido_update'),
    path('contenido/<int:pk>/eliminar/', views.contenido_delete, name='contenido_delete'),
    path('contenido/agregar-episodios/<int:contenido_id>/', views.agregar_episodios, name='agregar_episodios'),
    path('contenido/<int:contenido_id>/episodios/', views.contenido_gestion_episodios, name='contenido_gestion_episodios'),
    path('contenido/<int:contenido_id>/episodios/agregar/', views.episodio_create, name='episodio_create'),
    path('episodio/<int:episodio_id>/editar/', views.episodio_update, name='episodio_update'),
    path('episodio/<int:episodio_id>/eliminar/', views.episodio_delete, name='episodio_delete'),
    # Perfil
    path('perfil/', views.perfil_view, name='perfil'),
    # Activación de cuenta
    path('activar/<uidb64>/<token>/', views.activate_account, name='activate_account'),    # Recuperación de contraseña - Sistema completo
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    path('toggle-favorito/', views.toggle_favorito, name='toggle_favorito'),
    # Sistema de Rating/Like-Dislike
    path('toggle-like/', views.toggle_like, name='toggle_like'),
    path('toggle-dislike/', views.toggle_dislike, name='toggle_dislike'),
    path('get-user-rating/<int:contenido_id>/', views.get_user_rating, name='get_user_rating'),
    path('get-content-ratings/<int:contenido_id>/', views.get_content_ratings, name='get_content_ratings'), 
    path('busqueda/', views.busqueda, name='busqueda'),
    # Sistema de Recomendaciones
    path('recomendaciones/', views.recomendaciones_personalizadas, name='recomendaciones_personalizadas'),
    path('recomendaciones/categoria/<int:categoria_id>/', views.recomendaciones_categoria, name='recomendaciones_categoria'),
    path('contenido/<int:contenido_id>/similar/', views.contenido_similar, name='contenido_similar'),
    path('api/recomendaciones/', views.api_recomendaciones, name='api_recomendaciones'),
    path('admin/estadisticas-recomendaciones/', views.estadisticas_recomendaciones, name='estadisticas_recomendaciones'),
    # Sistema de Auditoría y Logs
    path('admin/audit-dashboard/', audit_views.audit_dashboard, name='audit_dashboard'),
    path('admin/audit-logs/', audit_views.audit_logs_view, name='audit_logs'),
    path('admin/session-monitoring/', audit_views.session_monitoring, name='session_monitoring'),
    path('admin/security-alerts/', audit_views.security_alerts, name='security_alerts'),
    path('admin/export-audit-logs/', audit_views.export_audit_logs, name='export_audit_logs'),
    path('api/audit-stats/', audit_views.audit_stats_api, name='audit_stats_api'),
]
