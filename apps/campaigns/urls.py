
from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('new/', views.campaign_create, name='campaign_create'),
    path('<int:pk>/edit/', views.campaign_edit, name='campaign_edit'),
    path('<int:pk>/send/', views.campaign_send, name='campaign_send'),
    path('<int:pk>/detail/', views.campaign_detail, name='campaign_detail'),
    path('templates/<int:pk>/content/', views.get_template_content, name='template_content'),
    path('log/<int:log_id>/update-status/', views.update_log_status, name='update_log_status'),
    path('auto-notifications/', views.notification_settings, name='notification_settings'),
]
