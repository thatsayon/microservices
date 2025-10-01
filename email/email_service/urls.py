from django.urls import path
from . import views

app_name = 'email_service'

urlpatterns = [
    # Email operations
    path('send', views.SendEmailView.as_view(), name='send_email'),
    path('status/<uuid:email_id>', views.EmailStatusView.as_view(), name='email_status'),
    path('history', views.EmailHistoryView.as_view(), name='email_history'),
    path('stats', views.EmailStatsView.as_view(), name='email_stats'),
    
    # Template management
    path('templates', views.EmailTemplateListView.as_view(), name='template_list'),
    path('templates/<uuid:template_id>', views.EmailTemplateDetailView.as_view(), name='template_detail'),
    
    # Health check
    path('health', views.HealthCheckView.as_view(), name='health_check'),
]
