"""
Production settings for Petição Brasil project.
"""
from .base import *
import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Database
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Security Settings - HTTPS/SSL
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Permissions Policy (Feature Policy)
PERMISSIONS_POLICY = {
    'geolocation': [],
    'microphone': [],
    'camera': [],
    'payment': [],
    'usb': [],
}

# Content Security Policy (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.tailwindcss.com",
    "https://challenges.cloudflare.com",
    "https://www.googletagmanager.com",  # Google Analytics
    "https://www.google-analytics.com",  # Google Analytics
)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com")
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
    "blob:",
    "https://www.google-analytics.com",  # Google Analytics
    "https://www.googletagmanager.com",  # Google Tag Manager
)
CSP_FONT_SRC = ("'self'", "https:", "data:")
CSP_CONNECT_SRC = (
    "'self'",
    "https:",
    "https://www.google-analytics.com",  # Google Analytics
    "https://analytics.google.com",  # Google Analytics 4
    "https://www.googletagmanager.com",  # Google Tag Manager
    "https://region1.google-analytics.com",  # Google Analytics (regional)
)
CSP_FRAME_SRC = ("'self'", "https://challenges.cloudflare.com")
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# CSRF Security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False  # Keep False for AJAX compatibility

# Password Validation - Extra Strict in Production
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increased from 8
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# AWS S3 Settings - Always use S3 in production
# AWS Credentials
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-west-2')

# S3 URL Configuration
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 24 hours cache for public files
}

# WhiteNoise Configuration for Static Files
# Add immutable flag and increase max-age for hashed files
WHITENOISE_MAX_AGE = 31536000  # 1 year for hashed files
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: True  # All files are versioned by manifest

# Security Settings
AWS_DEFAULT_ACL = None  # ACLs disabled - use bucket policy
AWS_S3_FILE_OVERWRITE = False  # Don't overwrite files with same name
AWS_S3_VERIFY = True  # Verify SSL certificates

# Signature Configuration (v4 required for newer regions)
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_ADDRESSING_STYLE = 'virtual'

# Media files storage - FORCE S3 in production
DEFAULT_FILE_STORAGE = 'config.storage_backends.MediaStorage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Static files (use WhiteNoise for static, S3 for media only)
# STATICFILES_STORAGE remains WhiteNoise for better performance

# Email Configuration
# Default to console backend if not configured
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)

# If using SendGrid or other SMTP
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@peticaobrasil.com.br')
SERVER_EMAIL = config('SERVER_EMAIL', default='admin@peticaobrasil.com.br')

# Cache Configuration for Production with SSL
import ssl

redis_url = config('REDIS_URL', default='redis://localhost:6379/0')

# Configure cache with SSL for Heroku Redis
if redis_url.startswith('rediss://'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url.replace('/0', '/1'),  # Use database 1 for cache
            'OPTIONS': {
                'ssl_cert_reqs': None,  # Skip SSL verification for Heroku Redis
            }
        }
    }
else:
    # Local development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url.replace('/0', '/1'),
        }
    }

# Celery Configuration for Production
# Heroku Redis uses self-signed certificates - configure SSL to accept them
# The connection is still encrypted, we just skip certificate validation
if redis_url.startswith('rediss://'):
    CELERY_BROKER_URL = redis_url
    CELERY_RESULT_BACKEND = redis_url
    CELERY_BROKER_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
    CELERY_REDIS_BACKEND_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
else:
    CELERY_BROKER_URL = redis_url
    CELERY_RESULT_BACKEND = redis_url

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Celery Beat Schedule for periodic tasks
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'verify-pending-signatures': {
        'task': 'apps.signatures.tasks.verify_pending_signatures',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-expired-petitions': {
        'task': 'apps.petitions.tasks.cleanup_expired_petitions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Daily CRL download and certificate updates
    'download-and-cache-crls': {
        'task': 'apps.signatures.tasks.download_and_cache_crls',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    'update-icp-brasil-certificates': {
        'task': 'apps.signatures.tasks.update_icp_brasil_certificates',
        'schedule': crontab(hour=3, minute=30),  # Daily at 3:30 AM UTC
    },
}

# Sentry Error Tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Logging Configuration with Structured Logging and Security Events
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',  # Use JSON formatter for better querying
        },
        'security': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'level': 'WARNING',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security.csrf': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.petitions': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.signatures': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.core.security': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Admin URL (can be changed for security)
ADMIN_URL = config('ADMIN_URL', default='admin/')
