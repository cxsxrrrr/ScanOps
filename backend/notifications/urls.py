"""URL configuration for notifications app."""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('config/', views.notification_config, name='config'),
    path('logs/', views.email_logs, name='logs'),
    path('send-report/', views.send_report, name='send-report'),
]
