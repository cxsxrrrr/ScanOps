"""URL configuration for administration app."""
from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('metrics/', views.dashboard_metrics, name='metrics'),
    path('cyber-map/', views.cyber_map_data, name='cyber-map'),
    path('errors/', views.recent_errors, name='errors'),
    path('scan-config/', views.scan_config, name='scan-config'),
    path('users/', views.user_list, name='users'),
    path('users/<int:pk>/', views.user_detail, name='user-detail'),
    path('organizations/', views.organization_list, name='organizations'),
    path('organizations/<int:pk>/', views.organization_detail, name='organization-detail'),
    path('organizations/<int:pk>/plan/', views.update_org_plan, name='update-org-plan'),
    path('analytics/organizations/', views.analytics_organizations, name='analytics-organizations'),
    path('analytics/organizations/<int:pk>/', views.analytics_organization_detail, name='analytics-organization-detail'),
    path('audit-logs/', views.audit_log_list, name='audit-logs'),
    path('audit-logs/actions/', views.admin_action_log_list, name='admin-action-logs'),
    path('reports/summary/', views.admin_report_summary, name='admin-report-summary'),
    path('reports/export/', views.admin_report_export, name='admin-report-export'),
]
