"""
Celery configuration for Petição Brasil project.
"""
import os
import ssl
from celery import Celery
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('democracia_direta')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery with SSL support for Heroku Redis
redis_url = config('REDIS_URL', default='redis://localhost:6379/0')

# SSL configuration for Heroku Redis (self-signed certificates)
if redis_url.startswith('rediss://'):
    app.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        broker_use_ssl={
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_check_hostname': False,
        },
        redis_backend_use_ssl={
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_check_hostname': False,
        },
        # Connection pool settings
        broker_pool_limit=10,
        broker_connection_retry=True,
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=10,
        # Result backend settings
        result_backend_transport_options={
            'master_name': 'mymaster',
            'retry_on_timeout': True,
            'socket_keepalive': True,
            'socket_keepalive_options': {
                1: 1,  # TCP_KEEPIDLE
                2: 1,  # TCP_KEEPINTVL
                3: 3,  # TCP_KEEPCNT
            },
        },
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='America/Sao_Paulo',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        # Ignore result by default to reduce Redis load
        task_ignore_result=False,
        result_expires=3600,  # Results expire after 1 hour
    )
else:
    app.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='America/Sao_Paulo',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
    )


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
