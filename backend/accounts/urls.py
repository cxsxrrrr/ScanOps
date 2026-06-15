"""URL configuration for accounts app."""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('verify/', views.verify_token, name='verify'),
    path('profile/', views.profile, name='profile'),
    path('organization/', views.organization_detail, name='organization'),
    path('organization/llm-config/', views.llm_config_view, name='llm-config'),
    path('accept-terms/', views.accept_terms, name='accept-terms'),
    path('team/', views.team_list, name='team-list'),
    path('team/leave/', views.leave_organization, name='team-leave'),
    path('invitations/', views.invitation_list, name='invitation-list'),
    path('invitations/<int:invitation_id>/revoke/', views.revoke_invitation, name='invitation-revoke'),
    path('invitations/<uuid:token>/info/', views.invitation_info, name='invitation-info'),
    path('invitations/<uuid:token>/accept/', views.accept_invitation, name='invitation-accept'),
    
    # Payments (Stripe)
    path('payments/create-checkout-session/', views.create_checkout_session, name='create-checkout-session'),
    path('payments/create-portal-session/', views.create_portal_session, name='create-portal-session'),
    path('payments/cancel-subscription/', views.cancel_subscription, name='cancel-subscription'),
    path('payments/webhook/', views.stripe_webhook, name='stripe-webhook'),
]
