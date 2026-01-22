# Democracia Direta - Deployment Checklist

**Project Phase:** Planning - Phase 8  
**Document Version:** 1.0  
**Last Updated:** November 23, 2025  
**Status:** Draft

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Static Files and Media](#static-files-and-media)
5. [Heroku Configuration](#heroku-configuration)
6. [External Services Setup](#external-services-setup)
7. [Migration Strategy](#migration-strategy)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Monitoring Setup](#monitoring-setup)
10. [Rollback Procedures](#rollback-procedures)
11. [Launch Timeline](#launch-timeline)

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests passing (unit + integration + E2E)
- [ ] Test coverage ≥ 85%
- [ ] Security scan (Bandit) passing
- [ ] Dependency vulnerability check (Safety) passing
- [ ] Code review completed
- [ ] No hardcoded secrets or credentials
- [ ] All TODO/FIXME comments resolved
- [ ] Documentation updated

### Django Configuration

- [ ] `DEBUG = False` in production settings
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] `SECRET_KEY` using environment variable
- [ ] Security headers enabled (HSTS, XSS, etc.)
- [ ] HTTPS redirect enabled
- [ ] Database connection using environment variable
- [ ] Email backend configured
- [ ] Logging configured for production
- [ ] Static files collection tested
- [ ] Media files upload tested

### Database

- [ ] Migrations reviewed and tested
- [ ] Database backup strategy defined
- [ ] Initial data fixtures prepared
- [ ] Category data loaded
- [ ] Database indexes optimized
- [ ] Database connection pooling configured

### Security

- [ ] LGPD compliance reviewed
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] SQL injection tests passed
- [ ] File upload validation tested
- [ ] Rate limiting configured
- [ ] Security headers verified
- [ ] SSL certificate valid

### Performance

- [ ] Database queries optimized (no N+1)
- [ ] Static files compressed
- [ ] CDN configured (optional)
- [ ] Caching strategy implemented
- [ ] Load testing completed
- [ ] Response time targets met (<2s)

---

## Environment Configuration

### Environment Variables

Create a `.env` file (never commit to git):

```bash
# Django Core
SECRET_KEY=your-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=democraciadireta.herokuapp.com,www.democraciadireta.org

# Database (Heroku provides DATABASE_URL automatically)
DATABASE_URL=postgres://user:password@host:5432/database

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@democraciadireta.org
SERVER_EMAIL=admin@democraciadireta.org

# AWS S3 for Media Files
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=democracia-direta-petitions
AWS_S3_REGION_NAME=sa-east-1

# Cloudflare Turnstile
TURNSTILE_SITE_KEY=your-turnstile-site-key
TURNSTILE_SECRET_KEY=your-turnstile-secret-key

# Celery (if using)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Sentry (Error Tracking)
SENTRY_DSN=your-sentry-dsn

# Application Settings
MAX_SIGNED_PDF_SIZE=10485760  # 10MB in bytes
```

### Production Settings File

```python
# democracia_direta_project/settings_production.py

import os
import dj_database_url
from .settings import *

# Security
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (S3)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'sa-east-1')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 3600

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@democraciadireta.org')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'admin@democraciadireta.org')

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/production.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'petitions': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Sentry (Error Tracking)
if os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
```

---

## Database Setup

### PostgreSQL on Heroku

```bash
# Create PostgreSQL addon (if not already created)
heroku addons:create heroku-postgresql:mini -a democraciadireta

# Verify database
heroku pg:info -a democraciadireta

# Get database credentials
heroku config:get DATABASE_URL -a democraciadireta
```

### Database Configuration

```python
# democracia_direta_project/settings.py - Database configuration snippet

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,  # Connection pooling
        conn_health_checks=True,  # Health checks
    )
}
```

### Required Database Extensions

```sql
-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
```

---

## Static Files and Media

### WhiteNoise for Static Files

```python
# requirements.txt
whitenoise==6.6.0

# pressiona/settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add after SecurityMiddleware
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### AWS S3 for Media Files

```bash
# Install dependencies
pip install boto3 django-storages

# Create S3 bucket
aws s3 mb s3://democracia-direta-petitions --region sa-east-1

# Set bucket policy (public read for petition PDFs)
# Use AWS Console or CLI to configure
```

**S3 Bucket Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::democracia-direta-petitions/petitions/*"
        },
        {
            "Sid": "PrivateSignatures",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::democracia-direta-petitions/signatures/*",
            "Condition": {
                "StringNotEquals": {
                    "aws:UserAgent": "pressiona-backend"
                }
            }
        }
    ]
}
```

### Collect Static Files

```bash
# Run before deployment
python manage.py collectstatic --noinput
```

---

## Heroku Configuration

### Procfile

```procfile
# Procfile

web: gunicorn democracia_direta_project.wsgi --log-file -
worker: celery -A democracia_direta_project worker --loglevel=info
```

### Runtime Configuration

```
# runtime.txt
python-3.11.6
```

### Additional Dependencies

```
# requirements.txt additions for Heroku

gunicorn==21.2.0
psycopg2-binary==2.9.9
dj-database-url==2.1.0
whitenoise==6.6.0
boto3==1.34.0
django-storages==1.14.2
sentry-sdk==1.39.1
```

### Heroku App Creation

```bash
# Create Heroku app
heroku create democraciadireta

# Add buildpacks
heroku buildpacks:add --index 1 heroku/python -a democraciadireta

# Set environment variables
heroku config:set DJANGO_SETTINGS_MODULE=democracia_direta_project.settings_production -a democraciadireta
heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())') -a democraciadireta
heroku config:set ALLOWED_HOSTS=democraciadireta.herokuapp.com -a democraciadireta
heroku config:set DEBUG=False -a democraciadireta

# AWS credentials
heroku config:set AWS_ACCESS_KEY_ID=your-key -a democraciadireta
heroku config:set AWS_SECRET_ACCESS_KEY=your-secret -a democraciadireta
heroku config:set AWS_STORAGE_BUCKET_NAME=democracia-direta-petitions -a democraciadireta

# Email (SendGrid)
heroku config:set EMAIL_HOST_USER=apikey -a democraciadireta
heroku config:set EMAIL_HOST_PASSWORD=your-sendgrid-api-key -a democraciadireta

# Cloudflare Turnstile
heroku config:set TURNSTILE_SITE_KEY=your-site-key -a democraciadireta
heroku config:set TURNSTILE_SECRET_KEY=your-secret-key -a democraciadireta
```

### Heroku Addons

```bash
# PostgreSQL (already created)
heroku addons:create heroku-postgresql:mini -a democraciadireta

# Redis (for Celery)
heroku addons:create heroku-redis:mini -a democraciadireta

# SendGrid (Email)
heroku addons:create sendgrid:starter -a democraciadireta

# Papertrail (Logging)
heroku addons:create papertrail:choklad -a democraciadireta

# Sentry (Error Tracking)
heroku addons:create sentry:f1 -a democraciadireta

# Verify addons
heroku addons -a democraciadireta
```

---

## External Services Setup

### 1. AWS S3 Setup

**Create IAM User:**
```bash
# Create IAM user with S3 access
aws iam create-user --user-name democraciadireta-s3-user

# Attach S3 policy
aws iam attach-user-policy --user-name democraciadireta-s3-user --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Create access key
aws iam create-access-key --user-name democraciadireta-s3-user
```

**Create S3 Bucket:**
```bash
# Create bucket
aws s3 mb s3://democracia-direta-petitions --region sa-east-1

# Enable versioning
aws s3api put-bucket-versioning --bucket democracia-direta-petitions --versioning-configuration Status=Enabled

# Configure lifecycle policy (optional - delete old files)
aws s3api put-bucket-lifecycle-configuration --bucket democracia-direta-petitions --lifecycle-configuration file://s3-lifecycle.json
```

**s3-lifecycle.json:**
```json
{
    "Rules": [
        {
            "Id": "DeleteOldRejectedSignatures",
            "Filter": {
                "Prefix": "signatures/rejected/"
            },
            "Status": "Enabled",
            "Expiration": {
                "Days": 90
            }
        }
    ]
}
```

### 2. SendGrid Email Setup

```bash
# Sign up at https://sendgrid.com
# Create API key with "Mail Send" permissions

# Verify sender email
# Add sender: noreply@democraciadireta.org

# Configure DNS records (SPF, DKIM)
# Add to your domain DNS:
# TXT record: v=spf1 include:sendgrid.net ~all
# CNAME records: s1._domainkey, s2._domainkey (provided by SendGrid)

# Test email
heroku run python manage.py shell -a democraciadireta
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'noreply@democraciadireta.org', ['your-email@example.com'])
```

### 3. Cloudflare Turnstile Setup

```bash
# 1. Go to https://dash.cloudflare.com/
# 2. Navigate to Turnstile
# 3. Create new site
#    - Site name: Democracia Direta
#    - Domain: democraciadireta.herokuapp.com (or custom domain)
#    - Widget mode: Managed
# 4. Copy Site Key and Secret Key
# 5. Add to Heroku config

heroku config:set TURNSTILE_SITE_KEY=your-site-key -a democraciadireta
heroku config:set TURNSTILE_SECRET_KEY=your-secret-key -a democraciadireta
```

### 4. Sentry Error Tracking

```bash
# 1. Sign up at https://sentry.io
# 2. Create new project: Django
# 3. Copy DSN
# 4. Add to Heroku

heroku config:set SENTRY_DSN=your-sentry-dsn -a democraciadireta
```

### 5. Redis Setup (for Celery)

```bash
# Heroku Redis addon provides REDIS_URL automatically
heroku config:get REDIS_URL -a democraciadireta

# Set Celery to use Redis
heroku config:set CELERY_BROKER_URL=$(heroku config:get REDIS_URL -a democraciadireta) -a democraciadireta
```

---

## Migration Strategy

### Initial Migration Plan

```bash
# 1. Review all migrations
python manage.py showmigrations

# 2. Check for conflicts
python manage.py makemigrations --check --dry-run

# 3. Create migration backup script
python manage.py dumpdata --natural-foreign --natural-primary > backup.json

# 4. Deploy migrations to Heroku
heroku run python manage.py migrate -a democraciadireta

# 5. Load initial data (categories)
heroku run python manage.py loaddata categories -a democraciadireta
```

### Category Fixture

```json
// petitions/fixtures/categories.json

[
    {
        "model": "petitions.category",
        "pk": 1,
        "fields": {
            "name": "Saúde",
            "slug": "saude",
            "description": "Petições relacionadas à saúde pública",
            "icon": "heart",
            "color": "#DC3545",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 2,
        "fields": {
            "name": "Educação",
            "slug": "educacao",
            "description": "Petições relacionadas à educação",
            "icon": "book",
            "color": "#007BFF",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 3,
        "fields": {
            "name": "Meio Ambiente",
            "slug": "meio-ambiente",
            "description": "Petições relacionadas ao meio ambiente",
            "icon": "leaf",
            "color": "#28A745",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 4,
        "fields": {
            "name": "Transporte",
            "slug": "transporte",
            "description": "Petições relacionadas ao transporte público",
            "icon": "bus",
            "color": "#FFC107",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 5,
        "fields": {
            "name": "Segurança",
            "slug": "seguranca",
            "description": "Petições relacionadas à segurança pública",
            "icon": "shield",
            "color": "#6C757D",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 6,
        "fields": {
            "name": "Cultura",
            "slug": "cultura",
            "description": "Petições relacionadas à cultura",
            "icon": "palette",
            "color": "#E83E8C",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 7,
        "fields": {
            "name": "Direitos Humanos",
            "slug": "direitos-humanos",
            "description": "Petições relacionadas aos direitos humanos",
            "icon": "users",
            "color": "#17A2B8",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 8,
        "fields": {
            "name": "Economia",
            "slug": "economia",
            "description": "Petições relacionadas à economia",
            "icon": "dollar-sign",
            "color": "#FD7E14",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 9,
        "fields": {
            "name": "Infraestrutura",
            "slug": "infraestrutura",
            "description": "Petições relacionadas à infraestrutura urbana",
            "icon": "building",
            "color": "#6610F2",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    },
    {
        "model": "petitions.category",
        "pk": 10,
        "fields": {
            "name": "Outros",
            "slug": "outros",
            "description": "Outras petições",
            "icon": "ellipsis-h",
            "color": "#6C757D",
            "is_active": true,
            "created_at": "2025-11-23T00:00:00Z"
        }
    }
]
```

### Migration Commands

```bash
# Create migrations
python manage.py makemigrations petitions

# Show migration SQL (review before applying)
python manage.py sqlmigrate petitions 0001

# Apply migrations
python manage.py migrate

# Load fixtures
python manage.py loaddata categories
```

---

## Post-Deployment Verification

### Deployment Checklist

```bash
# 1. Deploy to Heroku
git push heroku main

# 2. Run migrations
heroku run python manage.py migrate -a democraciadireta

# 3. Load initial data
heroku run python manage.py loaddata categories -a democraciadireta

# 4. Collect static files (if not automatic)
heroku run python manage.py collectstatic --noinput -a democraciadireta

# 5. Create superuser
heroku run python manage.py createsuperuser -a democraciadireta

# 6. Verify app is running
heroku ps -a democraciadireta

# 7. Check logs
heroku logs --tail -a democraciadireta
```

### Manual Testing Checklist

**Homepage:**
- [ ] Homepage loads correctly
- [ ] Navigation menu works
- [ ] Search bar functional
- [ ] Category filters work
- [ ] Petition cards display properly
- [ ] Responsive on mobile

**Petition Creation:**
- [ ] Login required
- [ ] Form validation works
- [ ] CAPTCHA functional
- [ ] PDF generated successfully
- [ ] Redirect to petition detail
- [ ] Petition visible in list

**Petition Detail:**
- [ ] Title and description display
- [ ] Progress bar accurate
- [ ] Sign button visible
- [ ] Recent signatures display
- [ ] Share buttons work

**Petition Signing:**
- [ ] PDF download works
- [ ] Upload form accessible
- [ ] File validation works
- [ ] Form validation works
- [ ] CAPTCHA functional
- [ ] Verification initiated
- [ ] Status page updates
- [ ] Email confirmation sent

**Admin Panel:**
- [ ] Admin login works
- [ ] Petitions manageable
- [ ] Signatures viewable
- [ ] Categories editable
- [ ] Flagged content queue works

### Automated Health Checks

```python
# petitions/views/health.py

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import boto3

def health_check(request):
    """
    Health check endpoint for monitoring.
    
    Returns 200 if all systems operational, 500 otherwise.
    """
    checks = {
        'database': False,
        'cache': False,
        's3': False,
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = True
    except Exception:
        pass
    
    # Cache check (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        checks['cache'] = cache.get('health_check') == 'ok'
    except Exception:
        pass
    
    # S3 check
    try:
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        checks['s3'] = True
    except Exception:
        pass
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 500
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
    }, status=status_code)
```

**Add to URLs:**
```python
# democracia_direta_project/urls.py
urlpatterns = [
    path('health/', health_check, name='health_check'),
    # ... other patterns
]
```

---

## Monitoring Setup

### 1. Application Performance Monitoring (Sentry)

**Configure Sentry:**
```python
# democracia_direta_project/settings_production.py

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    send_default_pii=False,  # Don't send PII
    environment='production',
    release=os.environ.get('HEROKU_SLUG_COMMIT', 'unknown'),
)
```

### 2. Log Aggregation (Papertrail)

```bash
# View logs
heroku addons:open papertrail -a democraciadireta

# Search logs
heroku logs --tail --app democraciadireta | grep ERROR
```

### 3. Uptime Monitoring

**Options:**
- UptimeRobot (free, external)
- Pingdom
- StatusCake

**Configure:**
```
URL to monitor: https://democraciadireta.herokuapp.com/health/
Check interval: 5 minutes
```

### 4. Custom Metrics (New Relic - Optional)

```bash
# Add New Relic addon
heroku addons:create newrelic:wayne -a democraciadireta

# Install agent
pip install newrelic

# Configure
heroku config:set NEW_RELIC_CONFIG_FILE=newrelic.ini -a democraciadireta
```

### 5. Database Monitoring

```bash
# Heroku Postgres metrics
heroku pg:diagnose -a democraciadireta

# Connection info
heroku pg:info -a democraciadireta

# Long-running queries
heroku pg:outliers -a democraciadireta
```

---

## Rollback Procedures

### Quick Rollback

```bash
# View releases
heroku releases -a democraciadireta

# Rollback to previous release
heroku rollback -a democraciadireta

# Rollback to specific version
heroku rollback v123 -a democraciadireta
```

### Database Rollback

```bash
# 1. Create backup before risky operations
heroku pg:backups:capture -a democraciadireta

# 2. Download backup
heroku pg:backups:download -a democraciadireta

# 3. If needed, restore backup
heroku pg:backups:restore b001 DATABASE_URL -a democraciadireta --confirm democraciadireta
```

### Migration Rollback

```bash
# Show migrations
heroku run python manage.py showmigrations -a democraciadireta

# Rollback specific migration
heroku run python manage.py migrate petitions 0005 -a democraciadireta

# Rollback all app migrations
heroku run python manage.py migrate petitions zero -a democraciadireta
```

### Emergency Procedures

**1. App is Down:**
```bash
# Check dyno status
heroku ps -a democraciadireta

# Restart dynos
heroku restart -a democraciadireta

# Scale up if needed
heroku ps:scale web=2 -a democraciadireta
```

**2. Database Issues:**
```bash
# Check database status
heroku pg:info -a democraciadireta

# Kill long-running queries
heroku pg:kill <pid> -a democraciadireta

# Reset connections
heroku pg:killall -a democraciadireta
```

**3. Memory Issues:**
```bash
# Check memory usage
heroku logs --tail --app democraciadireta | grep "Error R14"

# Upgrade dyno type
heroku ps:type web=standard-1x -a democraciadireta
```

---

## Launch Timeline

### Phase 1: Internal Testing (Week 1)

**Day 1-2:**
- [ ] Deploy to staging environment
- [ ] Run full test suite
- [ ] Load test data
- [ ] Verify all features work

**Day 3-4:**
- [ ] Internal team testing
- [ ] Fix critical bugs
- [ ] Performance optimization
- [ ] Security audit

**Day 5:**
- [ ] Documentation review
- [ ] Deploy to production (limited access)
- [ ] Smoke tests on production

### Phase 2: Beta Testing (Week 2)

**Day 6-8:**
- [ ] Invite beta testers (50 users)
- [ ] Monitor usage patterns
- [ ] Collect feedback
- [ ] Fix bugs

**Day 9-10:**
- [ ] Expand to 200 beta users
- [ ] Performance monitoring
- [ ] Load testing with real traffic
- [ ] Refine UX based on feedback

### Phase 3: Public Launch (Week 3)

**Day 11-12:**
- [ ] Final security review
- [ ] Press release preparation
- [ ] Social media content ready
- [ ] Support documentation complete

**Day 13:**
- [ ] Soft launch (no marketing)
- [ ] Monitor for issues
- [ ] Verify all systems stable

**Day 14:**
- [ ] Public announcement
- [ ] Marketing campaign launch
- [ ] Monitor server load
- [ ] 24/7 monitoring

**Day 15:**
- [ ] Review first 24 hours
- [ ] Address any issues
- [ ] Optimize based on usage
- [ ] Celebrate! 🎉

### Post-Launch (Ongoing)

**Week 4+:**
- [ ] Daily monitoring
- [ ] Weekly performance reviews
- [ ] Monthly security audits
- [ ] Continuous improvements
- [ ] Feature iterations based on user feedback

---

## Production Deployment Commands

### Initial Deployment

```bash
# 1. Push code to Heroku
git push heroku main

# 2. Run migrations
heroku run python manage.py migrate -a democraciadireta

# 3. Load initial data
heroku run python manage.py loaddata categories -a democraciadireta

# 4. Create superuser
heroku run python manage.py createsuperuser -a democraciadireta

# 5. Collect static files
heroku run python manage.py collectstatic --noinput -a democraciadireta

# 6. Verify deployment
heroku open -a democraciadireta
```

### Subsequent Deployments

```bash
# 1. Run tests locally
pytest

# 2. Commit changes
git add .
git commit -m "Feature: description"

# 3. Push to main
git push origin main

# 4. Deploy to Heroku
git push heroku main

# 5. Run migrations (if any)
heroku run python manage.py migrate -a democraciadireta

# 6. Clear cache (if needed)
heroku run python manage.py clear_cache -a democraciadireta

# 7. Restart workers (if using Celery)
heroku ps:restart worker -a democraciadireta

# 8. Monitor logs
heroku logs --tail -a democraciadireta
```

---

## Maintenance Mode

### Enable Maintenance Mode

```bash
# Enable maintenance page
heroku maintenance:on -a democraciadireta

# Verify
heroku maintenance -a democraciadireta
```

### Custom Maintenance Page

```html
<!-- static/maintenance.html -->

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Democracia Direta - Em Manutenção</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f5f5f5;
        }
        .container {
            text-align: center;
            padding: 2rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #0066CC;
        }
        p {
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Manutenção Programada</h1>
        <p>Estamos realizando melhorias no sistema.</p>
        <p>Voltaremos em breve!</p>
        <p><small>Previsão: 30 minutos</small></p>
    </div>
</body>
</html>
```

### Disable Maintenance Mode

```bash
# Disable maintenance page
heroku maintenance:off -a democraciadireta
```

---

## Security Hardening

### SSL/TLS Configuration

```bash
# Heroku provides SSL automatically for *.herokuapp.com

# For custom domain, add SSL certificate
heroku certs:auto:enable -a democraciadireta

# Verify SSL
heroku certs -a democraciadireta
```

### Security Headers Verification

```bash
# Test security headers
curl -I https://democraciadireta.herokuapp.com | grep -E "Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options"
```

### Regular Security Tasks

```bash
# Weekly: Update dependencies
pip list --outdated
pip install --upgrade <package>

# Weekly: Run security scan
bandit -r petitions/
safety check

# Monthly: Review logs for suspicious activity
heroku logs --tail -a democraciadireta | grep "security"

# Quarterly: Full security audit
# - Penetration testing
# - Code review
# - LGPD compliance check
```

---

## Backup Strategy

### Automated Backups

```bash
# Enable automatic daily backups (Heroku Postgres Standard+)
heroku pg:backups:schedule DATABASE_URL --at '02:00 America/Sao_Paulo' -a democraciadireta

# Verify schedule
heroku pg:backups:schedules -a democraciadireta
```

### Manual Backups

```bash
# Create manual backup
heroku pg:backups:capture -a democraciadireta

# List backups
heroku pg:backups -a democraciadireta

# Download backup
heroku pg:backups:download b001 -a democraciadireta

# Restore backup
heroku pg:backups:restore b001 DATABASE_URL -a democraciadireta --confirm democraciadireta
```

### Media Files Backup (S3)

```bash
# Enable S3 versioning (already configured)
aws s3api get-bucket-versioning --bucket democracia-direta-petitions

# Manual backup to another bucket
aws s3 sync s3://democracia-direta-petitions s3://democracia-direta-petitions-backup --region sa-east-1
```

---

## Final Checklist

### Pre-Launch

- [ ] All tests passing (100%)
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] Load testing completed
- [ ] Documentation complete
- [ ] Team trained
- [ ] Support procedures documented
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] SSL certificate valid
- [ ] Custom domain configured (if applicable)
- [ ] Email sending verified
- [ ] Error tracking configured (Sentry)
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] LGPD compliance verified

### Launch Day

- [ ] Final smoke tests
- [ ] All team members available
- [ ] Monitoring dashboards open
- [ ] Support channels ready
- [ ] Social media posts scheduled
- [ ] Press release sent
- [ ] Blog post published

### Post-Launch (First Week)

- [ ] Daily monitoring
- [ ] User feedback collection
- [ ] Bug triage and fixes
- [ ] Performance optimization
- [ ] Usage analytics review

---

**Document Status:** Complete. All 9 planning phases documented. Ready for implementation! 🚀

---

## Next Steps

1. **Review all planning documents** (00-08)
2. **Set up development environment**
3. **Create Django project: `democracia_direta_project` with `petitions` app**
4. **Implement models** (Phase 2)
5. **Build PDF generation** (Phase 3)
6. **Develop verification pipeline** (Phase 4)
7. **Create UI templates** (Phase 5)
8. **Implement security measures** (Phase 6)
9. **Write tests** (Phase 7)
10. **Deploy to production** (Phase 8)

---

**Good luck with the implementation! 🎯**
