from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('index/', views.index, name='index'),
    path('anime-details/', views.render_anime_details, name='anime_details'),
    path('anime-details/<int:contenido_id>/', views.anime_details, name='anime_details'),
    path('anime-watching/', views.render_anime_watching, name='anime_watching'),
    path('blog-details/', views.render_blog_details, name='blog_details'),
    path('blog/', views.render_blog, name='blog'),
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
    path('activar/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    # Password Reset
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('ver-episodio/<int:episodio_id>/', views.anime_watching, name='anime_watching'),
    path('toggle-favorito/', views.toggle_favorito, name='toggle_favorito'),
    path('busqueda/', views.busqueda, name='busqueda'),
]
