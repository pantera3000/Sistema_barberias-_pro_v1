
from django.urls import path
from . import views

app_name = 'stamps'

urlpatterns = [
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/<int:pk>/edit/', views.promotion_edit, name='promotion_edit'),
    path('assign/', views.assign_stamps, name='assign_stamps'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/<int:pk>/redeem/', views.redeem_card, name='redeem_card'),
]
