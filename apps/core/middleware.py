"""
Security middleware for the application.
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options (prevent clickjacking)
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (formerly Feature Policy)
        response['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'accelerometer=(), '
            'gyroscope=()'
        )
        
        return response


class FileUploadSecurityMiddleware(MiddlewareMixin):
    """
    Additional security checks for file uploads.
    """
    
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
    
    def process_request(self, request):
        if request.method in ['POST', 'PUT']:
            # Check total upload size
            if request.META.get('CONTENT_LENGTH'):
                content_length = int(request.META['CONTENT_LENGTH'])
                if content_length > self.MAX_UPLOAD_SIZE:
                    return HttpResponseForbidden(
                        'Upload muito grande. Tamanho máximo: 10MB'
                    )
        
        return None
