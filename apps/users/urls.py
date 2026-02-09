from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Gestión de Trabajadores
    path('workers/', views.worker_list, name='worker_list'),
    path('workers/new/', views.worker_create, name='worker_create'),
    path('workers/<int:pk>/edit/', views.worker_edit, name='worker_edit'),
]
