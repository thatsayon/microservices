from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .serializers import SendEmailSerializer, EmailLogSerializer, EmailTemplateSerializer
from .services import EmailService
from .tasks import send_email_task
from .models import EmailLog, EmailTemplate
import logging

logger = logging.getLogger(__name__)


class SendEmailView(APIView):
    """
    Send email endpoint - called by other microservices
    
    POST /api/v1/email/send
    """
    
    def post(self, request):
        """
        Send an email synchronously or asynchronously
        
        Request body:
        {
            "to_email": "user@example.com",
            "to_name": "John Doe",
            "subject": "Email subject",
            "body_html": "<h1>HTML content</h1>",
            "body_text": "Text content",
            "template_name": "welcome",
            "template_data": {"user_name": "John", "platform_name": "MyApp"},
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "service_name": "auth-service",
            "user_id": "user-uuid",
            "send_async": true
        }
        """
        serializer = SendEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        send_async = data.pop('send_async', True)
        
        try:
            if send_async:
                # Send via Celery (async)
                task = send_email_task.delay(**data)
                logger.info(f"Email queued with task ID: {task.id}")
                return Response({
                    "success": True,
                    "message": "Email queued for sending",
                    "task_id": task.id
                }, status=status.HTTP_202_ACCEPTED)
            else:
                # Send immediately (sync)
                result = EmailService.send_email(**data)
                return Response(result, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailStatusView(APIView):
    """
    Check email status by email_id
    
    GET /api/v1/email/status/<email_id>
    """
    
    def get(self, request, email_id):
        try:
            email_log = EmailLog.objects.get(id=email_id)
            serializer = EmailLogSerializer(email_log)
            return Response({
                "success": True,
                "data": serializer.data
            })
        except EmailLog.DoesNotExist:
            return Response({
                "success": False,
                "error": "Email not found"
            }, status=status.HTTP_404_NOT_FOUND)


class EmailHistoryView(APIView):
    """
    Get email history for a user or service
    
    GET /api/v1/email/history?user_id=xxx&service_name=xxx&status=xxx
    """
    
    def get(self, request):
        # Get query parameters
        user_id = request.query_params.get('user_id')
        service_name = request.query_params.get('service_name')
        email_status = request.query_params.get('status')
        to_email = request.query_params.get('to_email')
        
        # Build query
        queryset = EmailLog.objects.all()
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if service_name:
            queryset = queryset.filter(service_name=service_name)
        if email_status:
            queryset = queryset.filter(status=email_status)
        if to_email:
            queryset = queryset.filter(to_email=to_email)
        
        # Paginate
        page_size = int(request.query_params.get('page_size', 50))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        emails = queryset[start:end]
        
        serializer = EmailLogSerializer(emails, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        })


class EmailTemplateListView(APIView):
    """
    List all email templates
    
    GET /api/v1/templates
    """
    
    def get(self, request):
        templates = EmailTemplate.objects.filter(is_active=True)
        serializer = EmailTemplateSerializer(templates, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        })
    
    def post(self, request):
        """Create a new template"""
        serializer = EmailTemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmailTemplateDetailView(APIView):
    """
    Get, update, or delete a specific template
    
    GET/PUT/DELETE /api/v1/templates/<template_id>
    """
    
    def get(self, request, template_id):
        try:
            template = EmailTemplate.objects.get(id=template_id)
            serializer = EmailTemplateSerializer(template)
            return Response({
                "success": True,
                "data": serializer.data
            })
        except EmailTemplate.DoesNotExist:
            return Response({
                "success": False,
                "error": "Template not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, template_id):
        try:
            template = EmailTemplate.objects.get(id=template_id)
            serializer = EmailTemplateSerializer(template, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "success": True,
                    "data": serializer.data
                })
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except EmailTemplate.DoesNotExist:
            return Response({
                "success": False,
                "error": "Template not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, template_id):
        try:
            template = EmailTemplate.objects.get(id=template_id)
            template.delete()
            return Response({
                "success": True,
                "message": "Template deleted"
            })
        except EmailTemplate.DoesNotExist:
            return Response({
                "success": False,
                "error": "Template not found"
            }, status=status.HTTP_404_NOT_FOUND)


class HealthCheckView(APIView):
    """
    Health check endpoint
    
    GET /api/v1/health
    """
    
    def get(self, request):
        # Check database connection
        try:
            connection.ensure_connection()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Check Celery (optional)
        celery_status = "unknown"
        try:
            from .tasks import send_email_task
            # Try to inspect Celery
            celery_status = "available"
        except Exception:
            celery_status = "unavailable"
        
        return Response({
            "status": "healthy",
            "service": "email-service",
            "database": db_status,
            "celery": celery_status,
            "version": "1.0.0"
        })


class EmailStatsView(APIView):
    """
    Get email statistics
    
    GET /api/v1/email/stats
    """
    
    def get(self, request):
        from django.db.models import Count
        from .models import EmailStatus
        
        # Get counts by status
        stats = EmailLog.objects.values('status').annotate(count=Count('id'))
        
        # Get counts by service
        by_service = EmailLog.objects.values('service_name').annotate(count=Count('id'))
        
        # Get counts by provider
        by_provider = EmailLog.objects.values('provider').annotate(count=Count('id'))
        
        return Response({
            "success": True,
            "data": {
                "by_status": list(stats),
                "by_service": list(by_service),
                "by_provider": list(by_provider),
                "total_emails": EmailLog.objects.count()
            }
        })

