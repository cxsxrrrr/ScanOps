"""URL configuration for urls_manager app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'urls_manager'

router = DefaultRouter()
router.register('', views.URLAssetViewSet, basename='urlasset')

urlpatterns = [
    path('', include(router.urls)),
]
