"""URL configuration for reports app."""
from django.urls import path, re_path
from . import views

app_name = 'reports'

urlpatterns = [
    path('org/', views.org_report, name='org-report'),
    path('<int:scan_id>/', views.report_detail, name='detail'),
    path('<int:scan_id>/download/', views.download_report, name='download'),
    re_path(r'^(?P<scan_id>\d+)/download$', views.download_report, name='download-no-slash'),
]
