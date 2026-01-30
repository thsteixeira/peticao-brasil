"""
Context processors for making settings available in templates.
"""
from django.conf import settings


def site_settings(request):
    """
    Add site-wide settings to template context.
    """
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'TURNSTILE_SITE_KEY': settings.TURNSTILE_SITE_KEY,
        'TURNSTILE_ENABLED': settings.TURNSTILE_ENABLED,
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'GOOGLE_ANALYTICS_ENABLED': settings.GOOGLE_ANALYTICS_ENABLED,
    }
