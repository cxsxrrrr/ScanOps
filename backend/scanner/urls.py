"""URL configuration for scanner app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'scanner'

router = DefaultRouter()
router.register('list', views.ScanViewSet, basename='scan')

urlpatterns = [
    path('trigger/', views.trigger_scan, name='trigger'),
    path('', include(router.urls)),
]
