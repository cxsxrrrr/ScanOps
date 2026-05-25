"""URL configuration for accounts app."""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('verify/', views.verify_token, name='verify'),
    path('profile/', views.profile, name='profile'),
    path('organization/', views.organization_detail, name='organization'),
    path('accept-terms/', views.accept_terms, name='accept-terms'),
]
