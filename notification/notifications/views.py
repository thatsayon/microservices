from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer
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
        notification = serializer.save()
        data = NotificationSerializer(notification).data
        # Emit async event to user’s Socket.IO room
        asyncio.get_event_loop().create_task(
            sio.emit("new_notification", data, room=f"user_{notification.user_id}")
        )

