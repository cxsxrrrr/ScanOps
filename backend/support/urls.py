"""URL configuration for the support app."""
from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('tickets/', views.ticket_list_create, name='list-create'),
    path('tickets/<int:pk>/', views.ticket_detail, name='detail'),
    path('tickets/<int:pk>/messages/', views.ticket_add_message, name='add-message'),
]
