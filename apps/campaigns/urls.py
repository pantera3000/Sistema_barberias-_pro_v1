
from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('new/', views.campaign_create, name='campaign_create'),
    path('<int:pk>/send/', views.campaign_send, name='campaign_send'),
]
