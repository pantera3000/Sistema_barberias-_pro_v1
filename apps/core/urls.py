
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.tenant_dashboard, name='dashboard'),
    path('owner-control/', views.owner_dashboard, name='owner_dashboard'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('settings/', views.tenant_settings, name='tenant_settings'),
]
