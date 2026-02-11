
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.tenant_dashboard, name='dashboard'),
    path('owner-control/', views.owner_dashboard, name='owner_dashboard'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/export-daily-report/', views.export_daily_report, name='export_daily_report'),
    path('api/daily-activity/', views.daily_activity_api, name='daily_activity_api'),
    path('settings/', views.tenant_settings, name='tenant_settings'),
]
