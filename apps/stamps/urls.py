
from django.urls import path
from . import views

app_name = 'stamps'

urlpatterns = [
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/<int:pk>/edit/', views.promotion_edit, name='promotion_edit'),
    path('kiosk/<slug:slug>/', views.public_lookup, name='public_lookup'),
    path('assign/', views.assign_stamps, name='assign_stamps'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/<int:pk>/redeem/', views.redeem_card, name='redeem_card'),
    path('customers/<int:customer_id>/add-stamp/', views.add_stamp_customer, name='add_stamp_customer'),
    path('customers/<int:customer_id>/history/', views.customer_history, name='customer_history'),
    path('transactions/<int:pk>/undo/', views.undo_transaction, name='undo_transaction'),
    
    # Client side
    path('my-stamps/', views.my_stamps, name='my_stamps'),
    path('kiosk/', views.customer_kiosk, name='customer_kiosk'),
    path('my-stamps/request/<int:pk>/', views.request_redemption, name='request_redemption'),
    # API Management
    path('requests/', views.pending_requests_list, name='pending_requests_list'),
    path('scan/', views.qr_scanner, name='qr_scanner'),
    path('api/requests/pending/', views.get_pending_requests, name='get_pending_requests'),
    path('api/requests/<int:pk>/resolve/', views.resolve_stamp_request, name='resolve_stamp_request'),
    path('api/customer-nudge/', views.api_customer_nudge, name='api_customer_nudge'),
    path('assignment-success/<int:card_id>/', views.assignment_success, name='assignment_success'),
]
