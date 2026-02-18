"""URL configuration for administration app."""
from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('metrics/', views.dashboard_metrics, name='metrics'),
    path('errors/', views.recent_errors, name='errors'),
    path('scan-config/', views.scan_config, name='scan-config'),
    path('users/', views.user_list, name='users'),
]
