"""URL configuration for reports app."""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('<int:scan_id>/', views.report_detail, name='detail'),
    path('<int:scan_id>/download/', views.download_report, name='download'),
]
