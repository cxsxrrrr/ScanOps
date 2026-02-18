"""
URL configuration for Auditoría Web.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/urls/', include('urls_manager.urls')),
    path('api/scans/', include('scanner.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/admin/', include('administration.urls')),
]
