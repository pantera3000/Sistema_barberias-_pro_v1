"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from apps.core.views import dashboard_dispatch

from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('superadmin/', include('apps.superadmin.urls')),
    path('accounts/', include('apps.users.urls')),
    path('app/', include('apps.core.urls')),
    path('app/customers/', include('apps.customers.urls')),
    path('app/services/', include('apps.services.urls')),
    path('app/loyalty/', include('apps.loyalty.urls')),
    path('app/stamps/', include('apps.stamps.urls')),
    path('app/rewards/', include('apps.rewards.urls')),
    path('app/reports/', include('apps.reports.urls')),
    path('app/campaigns/', include('apps.campaigns.urls')),
    path('app/audit/', include('apps.audit.urls')),
    path('dashboard/', dashboard_dispatch, name='dashboard_dispatch'),
    path('q/<slug:slug>/', include('apps.stamps.public_urls')),
    path('', RedirectView.as_view(pattern_name='users:login'), name='home'),
]
