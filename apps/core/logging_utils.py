"""
Structured logging utilities for better observability.
"""
import logging
import json
import time
from functools import wraps
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_var = ContextVar('correlation_id', default=None)


class StructuredLogger:
    """
    Wrapper for Python logger to add structured logging capabilities.
    Logs are output in JSON format for easy parsing and querying.
    """
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def _log(self, level, message, **kwargs):
        """Internal method to log structured data"""
        log_data = {
            'message': message,
            'timestamp': time.time(),
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data['correlation_id'] = correlation_id
        
        # Add any additional context
        if kwargs:
            log_data['context'] = kwargs
        
        # Log as JSON string
        self.logger.log(level, json.dumps(log_data))
    
    def debug(self, message, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)


def log_execution_time(logger, operation_name):
    """
    Decorator to log execution time of functions/methods.
    
    Usage:
        @log_execution_time(logger, 'pdf_generation')
        def generate_pdf(petition):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{operation_name} completed successfully",
                    duration_seconds=duration,
                    function=func.__name__
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation_name} failed",
                    duration_seconds=duration,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        return wrapper
    return decorator


def log_model_event(logger, model_name, event_type, instance_id, **extra):
    """
    Log model lifecycle events (created, updated, deleted, etc.)
    
    Args:
        logger: StructuredLogger instance
        model_name: Name of the model (e.g., 'Petition', 'Signature')
        event_type: Type of event (e.g., 'created', 'updated', 'deleted')
        instance_id: ID or UUID of the instance
        **extra: Additional context to log
    """
    logger.info(
        f"{model_name} {event_type}",
        model=model_name,
        event=event_type,
        instance_id=str(instance_id),
        **extra
    )


def set_correlation_id(correlation_id):
    """Set correlation ID for the current context"""
    correlation_id_var.set(correlation_id)


def get_correlation_id():
    """Get correlation ID from the current context"""
    return correlation_id_var.get()


class CorrelationIdMiddleware:
    """
    Middleware to add correlation IDs to all requests.
    Helps trace a request through the entire system.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import uuid
        
        # Get correlation ID from header or generate new one
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID', str(uuid.uuid4()))
        
        # Set in context
        set_correlation_id(correlation_id)
        
        # Add to response headers
        response = self.get_response(request)
        response['X-Correlation-ID'] = correlation_id
        
        return response
