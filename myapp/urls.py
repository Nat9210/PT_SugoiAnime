from django.urls import path
from . import views

urlpatterns = [
    # Rutas de la aplicación
    path('', views.index, name='home'),
    path('index/', views.index, name='index'),
    path('anime-details/', views.render_anime_details, name='anime_details'),
    path('anime-details/<int:contenido_id>/', views.anime_details, name='anime_details'),
    path('anime-watching/<int:episodio_id>/', views.anime_watching, name='anime_watching'),
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
    path('activar/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    # Recuperación de contraseña
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('toggle-favorito/', views.toggle_favorito, name='toggle_favorito'),
    # Sistema de Rating/Like-Dislike
    path('toggle-like/', views.toggle_like, name='toggle_like'),
    path('toggle-dislike/', views.toggle_dislike, name='toggle_dislike'),
    path('get-user-rating/<int:contenido_id>/', views.get_user_rating, name='get_user_rating'),
    path('get-content-ratings/<int:contenido_id>/', views.get_content_ratings, name='get_content_ratings'), 
    path('busqueda/', views.busqueda, name='busqueda'),
]
