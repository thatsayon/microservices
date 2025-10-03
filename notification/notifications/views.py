from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer
from .tasks import send_notification_task
from .sio import sio
import asyncio


class NotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if not user_id:
            return Notification.objects.none()
        return Notification.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        notification = serializer.save(user_id=self.request.user.id)
        data = NotificationSerializer(notification).data
        send_notification_task.delay(data, str(notification.user_id))
