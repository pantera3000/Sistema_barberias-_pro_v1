
from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', views.master_search, name='master_search'),
    path('organizations/', views.organization_list, name='organization_list'),
    path('organization/new/', views.organization_create, name='organization_create'),
    path('organization/<int:pk>/edit/', views.organization_edit, name='organization_edit'),
    path('organization/<int:pk>/features/', views.organization_features, name='organization_features'),
    
    # Comunicados
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/new/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    
    # Planes
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/new/', views.plan_create, name='plan_create'),
    path('plans/<int:pk>/edit/', views.plan_edit, name='plan_edit'),
    
    # Monitor y Uso
    path('usage/', views.usage_monitor, name='usage_monitor'),
    
    # Auditoría Global
    path('audit/', views.global_audit_list, name='global_audit'),
]
