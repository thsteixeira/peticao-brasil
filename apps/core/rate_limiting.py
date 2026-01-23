"""
Rate limiting implementation for security.
Simple in-memory rate limiting (for production use Redis).
"""
import time
from collections import defaultdict
from django.http import HttpResponse
from django.core.cache import cache
from django.utils.decorators import method_decorator
from functools import wraps


class RateLimiter:
    """
    Simple rate limiter using Django cache.
    """
    
    def __init__(self, max_requests=60, window=60):
        """
        Args:
            max_requests: Maximum number of requests allowed
            window: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = window
    
    def is_rate_limited(self, key):
        """
        Check if the given key is rate limited.
        
        Args:
            key: Unique identifier (e.g., IP address, user ID)
            
        Returns:
            True if rate limited, False otherwise
        """
        cache_key = f'rate_limit:{key}'
        
        # Get current count
        count = cache.get(cache_key, 0)
        
        if count >= self.max_requests:
            return True
        
        # Increment count
        if count == 0:
            # First request in window
            cache.set(cache_key, 1, self.window)
        else:
            # Increment existing count
            cache.incr(cache_key)
        
        return False
    
    def get_rate_limit_response(self):
        """
        Return HTTP 429 response for rate limited requests.
        """
        response = HttpResponse(
            'Muitas requisições. Tente novamente em alguns instantes.',
            status=429
        )
        response['Retry-After'] = str(self.window)
        return response


def rate_limit(max_requests=60, window=60):
    """
    Decorator for rate limiting views.
    
    Usage:
        @rate_limit(max_requests=10, window=60)
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            limiter = RateLimiter(max_requests, window)
            
            # Use IP address as key
            ip = get_client_ip(request)
            
            if limiter.is_rate_limited(ip):
                return limiter.get_rate_limit_response()
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_client_ip(request):
    """
    Get the client's IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


# Predefined rate limiters for different use cases
class RateLimiters:
    """
    Predefined rate limiters for common use cases.
    """
    
    # Strict rate limit for authentication endpoints
    AUTH = RateLimiter(max_requests=5, window=300)  # 5 requests per 5 minutes
    
    # Moderate rate limit for API endpoints
    API = RateLimiter(max_requests=60, window=60)  # 60 requests per minute
    
    # Lenient rate limit for general views
    GENERAL = RateLimiter(max_requests=120, window=60)  # 120 requests per minute
    
    # Strict rate limit for file uploads
    UPLOAD = RateLimiter(max_requests=10, window=300)  # 10 uploads per 5 minutes
