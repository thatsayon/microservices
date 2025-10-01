from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class InternalAPIKeyMiddleware:
    """Validate internal API key for service-to-service communication"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for health check
        if request.path.endswith('/health'):
            return self.get_response(request)
        
        # Check API key for API endpoints
        if request.path.startswith('/api/'):
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                logger.warning(f"Missing API key for request: {request.path}")
                return JsonResponse({
                    "success": False,
                    "error": "Missing X-API-Key header"
                }, status=401)
            
            if api_key != settings.INTERNAL_API_KEY:
                logger.warning(f"Invalid API key attempt: {request.path}")
                return JsonResponse({
                    "success": False,
                    "error": "Invalid API key"
                }, status=401)
        
        return self.get_response(request)
