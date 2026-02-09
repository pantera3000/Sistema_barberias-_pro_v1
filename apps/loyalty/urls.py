
from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('assign/', views.assign_points, name='assign_points'),
]
