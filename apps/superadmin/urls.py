
from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('organization/new/', views.organization_create, name='organization_create'),
    path('organization/<int:pk>/edit/', views.organization_edit, name='organization_edit'),
    path('organization/<int:pk>/features/', views.organization_features, name='organization_features'),
]
