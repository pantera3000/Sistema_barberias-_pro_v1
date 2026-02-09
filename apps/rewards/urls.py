
from django.urls import path
from . import views

app_name = 'rewards'

urlpatterns = [
    path('catalog/', views.reward_list, name='reward_list'),
    path('catalog/<int:pk>/edit/', views.reward_edit, name='reward_edit'),
    path('redeem/', views.redeem_reward, name='redeem_reward'),
    path('history/', views.redemption_history, name='redemption_history'),
]
