
from django.urls import path
from . import views

app_name = 'stamps'

urlpatterns = [
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/<int:pk>/edit/', views.promotion_edit, name='promotion_edit'),
    path('assign/', views.assign_stamps, name='assign_stamps'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/<int:pk>/redeem/', views.redeem_card, name='redeem_card'),
    path('customers/<int:customer_id>/add-stamp/', views.add_stamp_customer, name='add_stamp_customer'),
    path('customers/<int:customer_id>/history/', views.customer_history, name='customer_history'),
    path('transactions/<int:pk>/undo/', views.undo_transaction, name='undo_transaction'),
    
    # Client side
    path('my-stamps/', views.my_stamps, name='my_stamps'),
    path('my-stamps/request/<int:pk>/', views.request_redemption, name='request_redemption'),
]
