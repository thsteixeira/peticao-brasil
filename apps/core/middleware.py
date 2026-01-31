"""
Security middleware for the application.
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger('apps.core.security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://challenges.cloudflare.com "
            "https://www.googletagmanager.com https://www.google-analytics.com "
            "https://googleads.g.doubleclick.net https://www.googleadservices.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data: https: blob: https://www.google-analytics.com https://www.googletagmanager.com "
            "https://googleads.g.doubleclick.net; "
            "font-src 'self' data:; "
            "connect-src 'self' https://challenges.cloudflare.com "
            "https://www.google-analytics.com https://analytics.google.com "
            "https://www.googletagmanager.com https://region1.google-analytics.com "
            "https://stats.g.doubleclick.net; "
            "frame-src 'self' https://challenges.cloudflare.com; "
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
                    logger.warning(
                        'Upload size exceeded',
                        extra={
                            'ip': self._get_client_ip(request),
                            'size': content_length,
                            'path': request.path,
                        }
                    )
                    return HttpResponseForbidden(
                        'Upload muito grande. Tamanho máximo: 10MB'
                    )
        
        return None
    
    def _get_client_ip(self, request):
        """Get the client's IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Log security-related events.
    """
    
    def process_request(self, request):
        # Log suspicious requests
        if self._is_suspicious(request):
            logger.warning(
                'Suspicious request detected',
                extra={
                    'ip': self._get_client_ip(request),
                    'path': request.path,
                    'method': request.method,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
        return None
    
    def process_exception(self, request, exception):
        # Log exceptions that might be security-related
        if isinstance(exception, (PermissionError, ValueError)):
            logger.error(
                f'Security exception: {exception.__class__.__name__}',
                extra={
                    'ip': self._get_client_ip(request),
                    'path': request.path,
                    'user': str(request.user) if request.user.is_authenticated else 'anonymous',
                    'exception': str(exception),
                },
                exc_info=True
            )
        return None
    
    def _is_suspicious(self, request):
        """
        Check if request has suspicious patterns.
        """
        suspicious_patterns = [
            '/admin/../',
            '/.env',
            '/wp-admin',
            '/phpMyAdmin',
            '/.git/',
            '/config.php',
            '/shell.php',
            '../',  # Path traversal
        ]
        
        path = request.path.lower()
        return any(pattern in path for pattern in suspicious_patterns)
    
    def _get_client_ip(self, request):
        """Get the client's IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def _get_client_ip(request):
    """Helper function to get client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Signal handlers for authentication events
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log successful login attempts.
    """
    logger.info(
        'User logged in',
        extra={
            'user': user.username,
            'ip': _get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Log failed login attempts.
    """
    logger.warning(
        'Failed login attempt',
        extra={
            'username': credentials.get('username', 'unknown'),
            'ip': _get_client_ip(request) if request else 'unknown',
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
        }
    )
