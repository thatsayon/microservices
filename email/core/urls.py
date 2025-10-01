from django.urls import path, include

urlpatterns = [
    path('email/', include('email_service.urls'))
]
