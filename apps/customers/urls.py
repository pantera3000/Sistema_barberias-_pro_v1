
from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('new/', views.customer_create, name='customer_create'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('birthdays/', views.birthday_list, name='birthday_list'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('login/<slug:slug>/', views.customer_login, name='customer_login'),
    
    # API for AJAX search and logging
    path('api/search/', views.customer_search_api, name='customer_search_api'),
    path('api/<int:pk>/log-whatsapp/', views.log_whatsapp_message, name='log_whatsapp_message'),
]
