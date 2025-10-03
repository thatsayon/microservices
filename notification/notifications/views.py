from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer
from .tasks import send_notification_task
import logging

logger = logging.getLogger(__name__)

class NotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]  # 👈 Add authentication
    
    def get_queryset(self):
        # Only return notifications for the authenticated user
        return Notification.objects.filter(user_id=self.request.user.id)
    
    def perform_create(self, serializer):
        # Ensure user can only create notifications for themselves
        notification = serializer.save(user_id=self.request.user.id)
        data = NotificationSerializer(notification).data
        
        # Send real-time notification
        send_notification_task.delay(data, str(notification.user_id))
        
        logger.info(f"Notification created for user {notification.user_id}: {notification.title}")

class NotificationMarkReadView(generics.UpdateAPIView):
    """Mark a notification as read"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user_id=self.request.user.id)
    
    def patch(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )

class NotificationMarkAllReadView(generics.GenericAPIView):
    """Mark all notifications as read for the authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        count = Notification.objects.filter(
            user_id=request.user.id,
            is_read=False
        ).update(is_read=True)
        
        return Response(
            {"message": f"{count} notifications marked as read"},
            status=status.HTTP_200_OK
        )
