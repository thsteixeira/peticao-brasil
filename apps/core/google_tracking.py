"""
Google Analytics helper functions for custom event tracking.
"""
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_ga_tracking_code(event_name, event_params=None):
    """
    Generate JavaScript code for Google Analytics custom event tracking.
    
    Args:
        event_name (str): Name of the event (e.g., 'petition_created', 'petition_signed')
        event_params (dict): Optional event parameters
        
    Returns:
        str: JavaScript code to track the event, or empty string if GA is disabled
        
    Example:
        >>> get_ga_tracking_code('petition_signed', {'petition_id': 123, 'value': 1})
    """
    if not settings.GOOGLE_ANALYTICS_ENABLED or not settings.GOOGLE_ANALYTICS_ID:
        return ''
    
    params = event_params or {}
    params_str = ', '.join([f"'{k}': '{v}'" for k, v in params.items()])
    
    return f"""
    <script>
      if (typeof gtag !== 'undefined') {{
        gtag('event', '{event_name}', {{{params_str}}});
      }}
    </script>
    """


class GoogleAnalyticsEventMixin:
    """
    Mixin for Django views to add Google Analytics event tracking.
    
    Usage:
        class PetitionCreateView(GoogleAnalyticsEventMixin, CreateView):
            ga_event_name = 'petition_created'
            
            def get_ga_event_params(self):
                return {
                    'petition_id': self.object.id,
                    'category': self.object.category
                }
    """
    ga_event_name = None
    ga_event_params = {}
    
    def get_ga_event_name(self):
        """Override this to dynamically set event name."""
        return self.ga_event_name
    
    def get_ga_event_params(self):
        """Override this to dynamically set event parameters."""
        return self.ga_event_params
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        event_name = self.get_ga_event_name()
        if event_name:
            event_params = self.get_ga_event_params()
            context['ga_tracking_code'] = get_ga_tracking_code(event_name, event_params)
        
        return context



