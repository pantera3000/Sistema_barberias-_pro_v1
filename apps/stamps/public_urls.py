from django.urls import path
from . import views

app_name = 'stamps_public'

urlpatterns = [
    path('', views.qr_request_stamp, name='qr_request'),
]
