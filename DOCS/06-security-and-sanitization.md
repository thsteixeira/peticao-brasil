# Democracia Direta - Security and Sanitization

**Project Phase:** Planning - Phase 6  
**Document Version:** 1.0  
**Last Updated:** November 23, 2025  
**Status:** Draft

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [File Upload Security](#file-upload-security)
3. [PDF Sanitization](#pdf-sanitization)
4. [Input Validation and Sanitization](#input-validation-and-sanitization)
5. [Authentication and Authorization](#authentication-and-authorization)
6. [Data Privacy (LGPD Compliance)](#data-privacy-lgpd-compliance)
7. [Rate Limiting and DDoS Protection](#rate-limiting-and-ddos-protection)
8. [Malware and Virus Scanning](#malware-and-virus-scanning)
9. [SQL Injection Prevention](#sql-injection-prevention)
10. [XSS and CSRF Protection](#xss-and-csrf-protection)
11. [Secure CPF Storage](#secure-cpf-storage)
12. [API Security](#api-security)
13. [Logging and Monitoring](#logging-and-monitoring)
14. [Incident Response Plan](#incident-response-plan)

---

## Security Overview

### Threat Model

**Primary Threats:**

1. **Malicious File Uploads**
   - PDF bombs (compressed payloads)
   - Embedded malware/exploits
   - JavaScript in PDFs
   - Corrupted/malformed PDFs

2. **Data Breaches**
   - CPF exposure
   - Email harvesting
   - User credential theft
   - Signature forgery

3. **Abuse and Spam**
   - Bot-driven petition creation
   - Automated signatures (fake)
   - Content spam/inappropriate material
   - DoS attacks

4. **Privacy Violations**
   - LGPD non-compliance
   - Unauthorized data access
   - Data retention violations
   - Cross-reference attacks

5. **Application Vulnerabilities**
   - SQL injection
   - XSS attacks
   - CSRF attacks
   - Path traversal
   - Insecure deserialization

### Security Principles

1. **Defense in Depth**
   - Multiple layers of security
   - No single point of failure
   - Fail securely by default

2. **Least Privilege**
   - Minimal permissions
   - Role-based access control
   - Time-limited access tokens

3. **Zero Trust**
   - Validate all inputs
   - Verify all outputs
   - Trust nothing by default

4. **Privacy by Design**
   - Minimize data collection
   - Anonymize where possible
   - Encrypt sensitive data

---

## File Upload Security

### Upload Restrictions

**Django Settings:**
```python
# pressiona/settings.py

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB in memory
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB total

# Allowed MIME types for petition signatures
ALLOWED_SIGNATURE_MIME_TYPES = [
    'application/pdf',
]

# Maximum file size for signed PDFs
MAX_SIGNED_PDF_SIZE = 10 * 1024 * 1024  # 10MB

# File storage configuration
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'sa-east-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Secure S3 bucket policy
AWS_S3_CUSTOM_DOMAIN = None  # Don't use CloudFront for security
AWS_QUERYSTRING_AUTH = True  # Use signed URLs
AWS_QUERYSTRING_EXPIRE = 3600  # URLs expire in 1 hour
```

### File Validator Class

```python
# pressionaapp/validators.py

import os
import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class SignedPDFValidator:
    """
    Comprehensive validator for uploaded signed PDF files.
    
    Validates:
    - File size
    - MIME type
    - File extension
    - PDF structure
    - Malicious content indicators
    """
    
    def __init__(self, max_size=None):
        self.max_size = max_size or settings.MAX_SIGNED_PDF_SIZE
    
    def __call__(self, file):
        """Validate the uploaded file."""
        self._validate_size(file)
        self._validate_extension(file)
        self._validate_mime_type(file)
        self._validate_pdf_structure(file)
        self._validate_content_safety(file)
    
    def _validate_size(self, file):
        """Check file size."""
        if file.size > self.max_size:
            raise ValidationError(
                _('O arquivo é muito grande. Tamanho máximo: %(max)s MB.'),
                params={'max': self.max_size / (1024 * 1024)},
                code='file_too_large'
            )
        
        if file.size == 0:
            raise ValidationError(
                _('O arquivo está vazio.'),
                code='empty_file'
            )
    
    def _validate_extension(self, file):
        """Check file extension."""
        ext = os.path.splitext(file.name)[1].lower()
        if ext != '.pdf':
            raise ValidationError(
                _('Tipo de arquivo inválido. Apenas arquivos PDF são aceitos.'),
                code='invalid_extension'
            )
    
    def _validate_mime_type(self, file):
        """Check MIME type using python-magic."""
        # Read first 2048 bytes for MIME detection
        file.seek(0)
        header = file.read(2048)
        file.seek(0)
        
        # Detect MIME type
        mime = magic.from_buffer(header, mime=True)
        
        if mime not in settings.ALLOWED_SIGNATURE_MIME_TYPES:
            raise ValidationError(
                _('Tipo de arquivo inválido. Detectado: %(mime)s'),
                params={'mime': mime},
                code='invalid_mime_type'
            )
    
    def _validate_pdf_structure(self, file):
        """Validate PDF structure basics."""
        file.seek(0)
        header = file.read(10)
        
        # Check PDF magic number
        if not header.startswith(b'%PDF-'):
            raise ValidationError(
                _('O arquivo não é um PDF válido.'),
                code='invalid_pdf_structure'
            )
        
        # Check PDF version (1.0 to 2.0)
        try:
            version_str = header[5:8].decode('ascii')
            version = float(version_str)
            if not (1.0 <= version <= 2.0):
                raise ValidationError(
                    _('Versão PDF não suportada: %(version)s'),
                    params={'version': version},
                    code='unsupported_pdf_version'
                )
        except (ValueError, UnicodeDecodeError):
            raise ValidationError(
                _('Cabeçalho PDF inválido.'),
                code='invalid_pdf_header'
            )
        
        file.seek(0)
    
    def _validate_content_safety(self, file):
        """Check for dangerous PDF content."""
        file.seek(0)
        content = file.read()
        file.seek(0)
        
        # Check for suspicious keywords (basic check)
        dangerous_patterns = [
            b'/JavaScript',
            b'/JS',
            b'/Launch',
            b'/OpenAction',
            b'/AA',  # Additional Actions
            b'/Names',
            b'/AcroForm',
            b'/XFA',  # XML Forms Architecture
        ]
        
        for pattern in dangerous_patterns:
            if pattern in content:
                # Not necessarily malicious, but flag for review
                raise ValidationError(
                    _('O PDF contém elementos que requerem revisão manual. '
                      'Entre em contato com o suporte.'),
                    code='suspicious_pdf_content'
                )
        
        # Check for excessive compression (PDF bomb indicator)
        compression_ratio = len(content) / file.size if file.size > 0 else 1
        if compression_ratio > 100:  # Suspiciously high compression
            raise ValidationError(
                _('O arquivo apresenta características suspeitas.'),
                code='suspicious_compression'
            )


def validate_signed_pdf(file):
    """Shortcut function for PDF validation."""
    validator = SignedPDFValidator()
    validator(file)
```

### Secure File Handling

```python
# pressionaapp/utils/file_handlers.py

import os
import uuid
import hashlib
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone


class SecureFileHandler:
    """
    Handles file uploads with security best practices.
    """
    
    @staticmethod
    def generate_secure_filename(original_filename, user_id=None):
        """
        Generate a secure filename that prevents path traversal.
        
        Format: signatures/{year}/{month}/{uuid}_{hash}.pdf
        """
        # Extract extension (already validated)
        ext = os.path.splitext(original_filename)[1].lower()
        
        # Generate UUID
        file_uuid = uuid.uuid4()
        
        # Hash original filename for uniqueness
        filename_hash = hashlib.md5(
            original_filename.encode('utf-8')
        ).hexdigest()[:8]
        
        # Build path
        now = timezone.now()
        path = os.path.join(
            'signatures',
            str(now.year),
            str(now.month).zfill(2),
            f'{file_uuid}_{filename_hash}{ext}'
        )
        
        return path
    
    @staticmethod
    def save_uploaded_file(file, user_id=None):
        """
        Save uploaded file to secure storage.
        
        Returns:
            tuple: (storage_path, file_size, file_hash)
        """
        # Generate secure path
        storage_path = SecureFileHandler.generate_secure_filename(
            file.name, 
            user_id
        )
        
        # Read file content
        file.seek(0)
        content = file.read()
        
        # Calculate SHA-256 hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Save to storage (S3)
        saved_path = default_storage.save(
            storage_path,
            ContentFile(content)
        )
        
        return saved_path, len(content), file_hash
    
    @staticmethod
    def delete_file(storage_path):
        """Safely delete file from storage."""
        if default_storage.exists(storage_path):
            default_storage.delete(storage_path)
    
    @staticmethod
    def get_signed_url(storage_path, expiry=3600):
        """
        Generate temporary signed URL for file access.
        
        Args:
            storage_path: Path in S3
            expiry: URL validity in seconds (default 1 hour)
        
        Returns:
            str: Signed URL
        """
        return default_storage.url(storage_path)
```

---

## PDF Sanitization

### PDF Processing Pipeline

```python
# pressionaapp/services/pdf_sanitizer.py

import io
import PyPDF2
from PIL import Image
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class PDFSanitizer:
    """
    Sanitizes PDF files by removing potentially dangerous elements.
    
    Note: For signed PDFs, sanitization may invalidate signatures.
    Use this BEFORE signing or for verification purposes only.
    """
    
    def __init__(self, pdf_file):
        """
        Initialize sanitizer with PDF file.
        
        Args:
            pdf_file: File-like object or path
        """
        self.pdf_file = pdf_file
        self.reader = None
        self.writer = None
    
    def sanitize(self):
        """
        Sanitize PDF by removing dangerous elements.
        
        Returns:
            io.BytesIO: Sanitized PDF content
        """
        # Read PDF
        self.pdf_file.seek(0)
        self.reader = PyPDF2.PdfReader(self.pdf_file)
        self.writer = PyPDF2.PdfWriter()
        
        # Process each page
        for page_num in range(len(self.reader.pages)):
            page = self.reader.pages[page_num]
            
            # Remove JavaScript
            if '/AA' in page:
                del page['/AA']
            if '/OpenAction' in page:
                del page['/OpenAction']
            
            # Add sanitized page
            self.writer.add_page(page)
        
        # Remove document-level JavaScript
        if self.reader.trailer.get('/Root'):
            root = self.reader.trailer['/Root']
            if '/AA' in root:
                del root['/AA']
            if '/OpenAction' in root:
                del root['/OpenAction']
            if '/Names' in root:
                # Remove JavaScript in Names dictionary
                names = root['/Names']
                if '/JavaScript' in names:
                    del names['/JavaScript']
        
        # Write to buffer
        output = io.BytesIO()
        self.writer.write(output)
        output.seek(0)
        
        return output
    
    def analyze_threats(self):
        """
        Analyze PDF for potential threats without modifying.
        
        Returns:
            dict: Threat analysis results
        """
        self.pdf_file.seek(0)
        self.reader = PyPDF2.PdfReader(self.pdf_file)
        
        threats = {
            'has_javascript': False,
            'has_launch_actions': False,
            'has_embedded_files': False,
            'has_forms': False,
            'encryption_status': None,
            'page_count': len(self.reader.pages),
            'metadata': {},
        }
        
        # Check for JavaScript
        for page in self.reader.pages:
            if '/AA' in page or '/OpenAction' in page:
                threats['has_javascript'] = True
                break
        
        # Check document-level threats
        if self.reader.trailer.get('/Root'):
            root = self.reader.trailer['/Root']
            
            if '/AA' in root or '/OpenAction' in root:
                threats['has_javascript'] = True
            
            if '/Names' in root:
                names = root['/Names']
                if '/JavaScript' in names:
                    threats['has_javascript'] = True
                if '/EmbeddedFiles' in names:
                    threats['has_embedded_files'] = True
            
            if '/AcroForm' in root:
                threats['has_forms'] = True
        
        # Check encryption
        if self.reader.is_encrypted:
            threats['encryption_status'] = 'encrypted'
        else:
            threats['encryption_status'] = 'not_encrypted'
        
        # Extract metadata
        if self.reader.metadata:
            threats['metadata'] = {
                'title': self.reader.metadata.get('/Title', ''),
                'author': self.reader.metadata.get('/Author', ''),
                'subject': self.reader.metadata.get('/Subject', ''),
                'creator': self.reader.metadata.get('/Creator', ''),
                'producer': self.reader.metadata.get('/Producer', ''),
            }
        
        return threats
```

---

## Input Validation and Sanitization

### Form Validators

```python
# pressionaapp/validators.py

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from validate_docbr import CPF


def validate_cpf(value):
    """
    Validate Brazilian CPF.
    
    Accepts formats:
    - 12345678901
    - 123.456.789-01
    """
    cpf_validator = CPF()
    
    # Remove formatting
    cpf_clean = re.sub(r'[^\d]', '', value)
    
    if not cpf_validator.validate(cpf_clean):
        raise ValidationError(
            _('CPF inválido.'),
            code='invalid_cpf'
        )
    
    return cpf_clean


def validate_brazilian_name(value):
    """
    Validate Brazilian full name.
    
    Requirements:
    - At least 2 words (first and last name)
    - Only letters, spaces, hyphens, apostrophes
    - 3-100 characters total
    """
    # Remove extra whitespace
    name = ' '.join(value.split())
    
    # Check length
    if len(name) < 3 or len(name) > 100:
        raise ValidationError(
            _('O nome deve ter entre 3 e 100 caracteres.'),
            code='invalid_name_length'
        )
    
    # Check for at least 2 words
    words = name.split()
    if len(words) < 2:
        raise ValidationError(
            _('Informe o nome completo (nome e sobrenome).'),
            code='incomplete_name'
        )
    
    # Check characters
    pattern = r'^[A-Za-zÀ-ÿ\s\'-]+$'
    if not re.match(pattern, name):
        raise ValidationError(
            _('O nome contém caracteres inválidos.'),
            code='invalid_name_characters'
        )
    
    return name


def validate_brazilian_city(value):
    """Validate Brazilian city name."""
    # Remove extra whitespace
    city = ' '.join(value.split())
    
    # Check length
    if len(city) < 2 or len(city) > 100:
        raise ValidationError(
            _('Nome da cidade inválido.'),
            code='invalid_city'
        )
    
    # Check characters (allow letters, spaces, hyphens)
    pattern = r'^[A-Za-zÀ-ÿ\s\'-]+$'
    if not re.match(pattern, city):
        raise ValidationError(
            _('Nome da cidade contém caracteres inválidos.'),
            code='invalid_city_characters'
        )
    
    return city


def validate_petition_title(value):
    """
    Validate petition title.
    
    Requirements:
    - 10-200 characters
    - No HTML tags
    - No excessive punctuation
    """
    # Check length
    if len(value) < 10:
        raise ValidationError(
            _('O título deve ter pelo menos 10 caracteres.'),
            code='title_too_short'
        )
    
    if len(value) > 200:
        raise ValidationError(
            _('O título deve ter no máximo 200 caracteres.'),
            code='title_too_long'
        )
    
    # Check for HTML tags
    if re.search(r'<[^>]+>', value):
        raise ValidationError(
            _('O título não pode conter tags HTML.'),
            code='html_in_title'
        )
    
    # Check for excessive punctuation
    if re.search(r'[!?]{3,}', value):
        raise ValidationError(
            _('Evite pontuação excessiva no título.'),
            code='excessive_punctuation'
        )
    
    return value.strip()


def validate_petition_description(value):
    """
    Validate petition description.
    
    Requirements:
    - 100-10,000 characters
    - No HTML tags (or sanitize)
    - No URLs (or limit)
    """
    # Check length
    if len(value) < 100:
        raise ValidationError(
            _('A descrição deve ter pelo menos 100 caracteres.'),
            code='description_too_short'
        )
    
    if len(value) > 10000:
        raise ValidationError(
            _('A descrição deve ter no máximo 10.000 caracteres.'),
            code='description_too_long'
        )
    
    # Check for HTML tags
    if re.search(r'<[^>]+>', value):
        raise ValidationError(
            _('A descrição não pode conter tags HTML.'),
            code='html_in_description'
        )
    
    # Check for excessive URLs
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, value)
    if len(urls) > 5:
        raise ValidationError(
            _('Limite de 5 URLs na descrição.'),
            code='too_many_urls'
        )
    
    return value.strip()


def validate_signature_goal(value):
    """
    Validate petition signature goal.
    
    Range: 10 to 1,000,000
    """
    if value < 10:
        raise ValidationError(
            _('A meta deve ser de pelo menos 10 assinaturas.'),
            code='goal_too_low'
        )
    
    if value > 1000000:
        raise ValidationError(
            _('A meta não pode exceder 1.000.000 de assinaturas.'),
            code='goal_too_high'
        )
    
    return value
```

### HTML Sanitization

```python
# pressionaapp/utils/sanitizers.py

import bleach
from django.utils.html import escape


class HTMLSanitizer:
    """
    Sanitize HTML content to prevent XSS attacks.
    """
    
    # Allowed tags for rich text (if implemented)
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
        'h3', 'h4', 'blockquote'
    ]
    
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
    }
    
    @staticmethod
    def sanitize_html(content):
        """
        Sanitize HTML content.
        
        For now, we strip all HTML. If rich text is needed,
        use bleach to allow specific tags.
        """
        # Option 1: Strip all HTML (current approach)
        return bleach.clean(content, tags=[], strip=True)
        
        # Option 2: Allow specific tags (future)
        # return bleach.clean(
        #     content,
        #     tags=HTMLSanitizer.ALLOWED_TAGS,
        #     attributes=HTMLSanitizer.ALLOWED_ATTRIBUTES,
        #     strip=True
        # )
    
    @staticmethod
    def sanitize_text(content):
        """
        Sanitize plain text by escaping HTML entities.
        """
        return escape(content)
```

---

## Authentication and Authorization

### Permission System

```python
# pressionaapp/permissions.py

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from functools import wraps


def petition_creator_required(view_func):
    """
    Decorator to ensure user is the creator of the petition.
    
    Usage:
        @petition_creator_required
        def edit_petition(request, petition_id):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, petition_id, *args, **kwargs):
        from pressionaapp.models import Petition
        
        try:
            petition = Petition.objects.get(pk=petition_id)
        except Petition.DoesNotExist:
            raise PermissionDenied("Petição não encontrada.")
        
        if petition.creator != request.user:
            raise PermissionDenied(
                "Você não tem permissão para modificar esta petição."
            )
        
        return view_func(request, petition_id, *args, **kwargs)
    
    return wrapper


def can_moderate_petition(user, petition=None):
    """
    Check if user can moderate petitions.
    
    Moderators: Staff users or petition creator
    """
    if user.is_staff or user.is_superuser:
        return True
    
    if petition and petition.creator == user:
        return True
    
    return False


def can_close_petition(user, petition):
    """
    Check if user can close a petition.
    
    Only creator can close their own petition.
    Staff can close any petition.
    """
    if user.is_staff or user.is_superuser:
        return True
    
    if petition.creator == user:
        return True
    
    return False
```

### Session Security

```python
# pressiona/settings.py

# Session security
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False

# CSRF protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False  # Use cookie

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## Data Privacy (LGPD Compliance)

### LGPD Requirements

**Legal Basis for Data Processing:**

1. **Petition Creation** (Art. 7, I - Consent)
   - User consent via terms checkbox
   - Clear purpose explanation
   - Optional fields clearly marked

2. **Petition Signing** (Art. 7, IX - Legitimate Interest)
   - Legitimate interest: democratic participation
   - Minimal data collection
   - Privacy options provided

3. **Signature Verification** (Art. 7, II - Legal Obligation)
   - Legal obligation to verify authenticity
   - ICP-Brasil standard compliance

### Privacy Configuration

```python
# pressionaapp/privacy.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class PrivacySettings:
    """
    User privacy settings for petition signatures.
    """
    show_full_name: bool = False  # Default: show initials only
    show_email: bool = False  # Never show publicly
    show_location: bool = True  # Show city/state
    receive_updates: bool = False  # Email notifications
    
    @classmethod
    def from_form(cls, form_data):
        """Create from form data."""
        return cls(
            show_full_name=form_data.get('show_full_name', False),
            show_email=False,  # Never allow
            show_location=form_data.get('show_location', True),
            receive_updates=form_data.get('receive_updates', False),
        )
    
    def display_name(self, full_name: str) -> str:
        """
        Return display name based on privacy settings.
        
        Examples:
            "João Silva" -> "João S." (initials)
            "João Silva" -> "João Silva" (full name if opted in)
        """
        if self.show_full_name:
            return full_name
        
        parts = full_name.split()
        if len(parts) < 2:
            return full_name
        
        # Show first name + last name initial
        return f"{parts[0]} {parts[-1][0]}."


class DataRetentionPolicy:
    """
    LGPD Article 15: Data retention policy.
    """
    
    # Retention periods (in days)
    ACTIVE_PETITION_DATA = None  # Keep while petition is active
    COMPLETED_PETITION_DATA = 1825  # 5 years after completion
    REJECTED_SIGNATURE_DATA = 90  # 90 days
    FLAGGED_CONTENT_DATA = 365  # 1 year
    
    @staticmethod
    def should_delete_signature(signature):
        """
        Determine if signature data should be deleted.
        
        LGPD Art. 16: Right to deletion
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Keep if petition is active
        if signature.petition.status == 'active':
            return False
        
        # Delete rejected signatures after 90 days
        if signature.verification_status == 'rejected':
            delete_after = signature.updated_at + timedelta(
                days=DataRetentionPolicy.REJECTED_SIGNATURE_DATA
            )
            return timezone.now() > delete_after
        
        # Delete approved signatures 5 years after petition completion
        if signature.petition.status in ['completed', 'closed']:
            delete_after = signature.petition.updated_at + timedelta(
                days=DataRetentionPolicy.COMPLETED_PETITION_DATA
            )
            return timezone.now() > delete_after
        
        return False
    
    @staticmethod
    def anonymize_signature(signature):
        """
        Anonymize signature data instead of deletion.
        
        Keeps statistical data while removing personal info.
        """
        # Keep: petition_id, created_at, city, state
        # Remove: cpf_hash, name, email, pdf_file, certificate_info
        
        signature.cpf_hash = None
        signature.name = "[Removido]"
        signature.email = None
        signature.pdf_file = None
        signature.certificate_info = {}
        signature.save()
```

### Data Access Rights (LGPD Art. 18)

```python
# pressionaapp/views/privacy_views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from pressionaapp.models import Petition, Signature
import csv
import json


@login_required
@require_http_methods(["GET"])
def download_my_data(request):
    """
    LGPD Art. 18, II: Right to access personal data.
    
    Export all user data in JSON format.
    """
    user = request.user
    
    # Collect all user data
    data = {
        'user_info': {
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined.isoformat(),
        },
        'petitions_created': [],
        'petitions_signed': [],
    }
    
    # Petitions created
    petitions = Petition.objects.filter(creator=user)
    for petition in petitions:
        data['petitions_created'].append({
            'id': petition.uuid,
            'title': petition.title,
            'created_at': petition.created_at.isoformat(),
            'status': petition.status,
            'signature_count': petition.signature_count,
        })
    
    # Petitions signed
    signatures = Signature.objects.filter(email=user.email)
    for signature in signatures:
        data['petitions_signed'].append({
            'petition_title': signature.petition.title,
            'signed_at': signature.created_at.isoformat(),
            'status': signature.verification_status,
        })
    
    # Return as JSON download
    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="meus_dados.json"'
    
    return response


@login_required
@require_http_methods(["POST"])
def delete_my_account(request):
    """
    LGPD Art. 18, VI: Right to deletion.
    
    Delete user account and associated data.
    """
    user = request.user
    
    # Check if user has active petitions
    active_petitions = Petition.objects.filter(
        creator=user,
        status='active'
    ).count()
    
    if active_petitions > 0:
        return JsonResponse({
            'error': 'Você tem petições ativas. Encerre-as antes de deletar sua conta.'
        }, status=400)
    
    # Anonymize signatures instead of deletion
    signatures = Signature.objects.filter(email=user.email)
    for signature in signatures:
        DataRetentionPolicy.anonymize_signature(signature)
    
    # Delete or anonymize petitions
    petitions = Petition.objects.filter(creator=user)
    for petition in petitions:
        if petition.signature_count > 0:
            # Anonymize creator
            petition.creator = None
            petition.save()
        else:
            # Delete if no signatures
            petition.delete()
    
    # Delete user account
    user.delete()
    
    return JsonResponse({
        'message': 'Conta deletada com sucesso.'
    })
```

---

## Rate Limiting and DDoS Protection

### Django Rate Limiting

```python
# pressionaapp/middleware/rate_limit.py

import time
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.translation import gettext as _


class RateLimitMiddleware:
    """
    Rate limiting middleware using Django cache.
    
    Limits:
    - Petition creation: 5 per hour per user
    - Signature upload: 10 per hour per IP
    - API calls: 100 per hour per IP
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Apply rate limiting to specific paths
        if request.path.startswith('/peticoes/criar/'):
            if not self._check_petition_creation_limit(request):
                return HttpResponseForbidden(
                    _('Limite de criação de petições excedido. '
                      'Aguarde 1 hora.')
                )
        
        elif request.path.startswith('/peticoes/') and '/upload/' in request.path:
            if not self._check_signature_upload_limit(request):
                return HttpResponseForbidden(
                    _('Limite de envios excedido. Aguarde alguns minutos.')
                )
        
        response = self.get_response(request)
        return response
    
    def _check_petition_creation_limit(self, request):
        """5 petitions per hour per user."""
        if not request.user.is_authenticated:
            return True  # Login required anyway
        
        key = f'petition_create_{request.user.id}'
        count = cache.get(key, 0)
        
        if count >= 5:
            return False
        
        cache.set(key, count + 1, 3600)  # 1 hour
        return True
    
    def _check_signature_upload_limit(self, request):
        """10 uploads per hour per IP."""
        ip = self._get_client_ip(request)
        key = f'signature_upload_{ip}'
        count = cache.get(key, 0)
        
        if count >= 10:
            return False
        
        cache.set(key, count + 1, 3600)  # 1 hour
        return True
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### Cloudflare Integration

```python
# pressiona/settings.py

# Cloudflare Turnstile (already implemented)
TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY')
TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY')

# Use Turnstile for:
# - Petition creation
# - Signature submission
# - Contact forms
```

---

## Malware and Virus Scanning

### ClamAV Integration

```python
# pressionaapp/services/malware_scanner.py

import pyclamd
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MalwareScanner:
    """
    Scan uploaded files for malware using ClamAV.
    
    Installation:
        # Ubuntu/Debian
        sudo apt-get install clamav clamav-daemon
        pip install pyclamd
        
        # Start daemon
        sudo systemctl start clamav-daemon
    """
    
    def __init__(self):
        try:
            self.cd = pyclamd.ClamdUnixSocket()
            # Test connection
            if not self.cd.ping():
                logger.error("ClamAV daemon not running")
                self.cd = None
        except Exception as e:
            logger.error(f"ClamAV connection error: {e}")
            self.cd = None
    
    def scan_file(self, file_path):
        """
        Scan file for malware.
        
        Returns:
            dict: {
                'is_clean': bool,
                'threat_name': str or None,
                'error': str or None
            }
        """
        if not self.cd:
            # ClamAV not available, skip scan
            logger.warning("ClamAV not available, skipping scan")
            return {
                'is_clean': True,  # Assume clean if scanner unavailable
                'threat_name': None,
                'error': 'Scanner unavailable'
            }
        
        try:
            result = self.cd.scan_file(file_path)
            
            if result is None:
                # Clean file
                return {
                    'is_clean': True,
                    'threat_name': None,
                    'error': None
                }
            else:
                # Threat detected
                threat_name = result[file_path][1] if file_path in result else 'Unknown'
                logger.warning(f"Malware detected: {threat_name} in {file_path}")
                return {
                    'is_clean': False,
                    'threat_name': threat_name,
                    'error': None
                }
        
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
            return {
                'is_clean': False,  # Fail closed
                'threat_name': None,
                'error': str(e)
            }
    
    def scan_stream(self, file_content):
        """
        Scan file content (bytes) for malware.
        
        Useful for in-memory scanning before storage.
        """
        if not self.cd:
            return {
                'is_clean': True,
                'threat_name': None,
                'error': 'Scanner unavailable'
            }
        
        try:
            result = self.cd.scan_stream(file_content)
            
            if result is None:
                return {
                    'is_clean': True,
                    'threat_name': None,
                    'error': None
                }
            else:
                threat_name = result.get('stream', ['', 'Unknown'])[1]
                logger.warning(f"Malware detected in stream: {threat_name}")
                return {
                    'is_clean': False,
                    'threat_name': threat_name,
                    'error': None
                }
        
        except Exception as e:
            logger.error(f"ClamAV stream scan error: {e}")
            return {
                'is_clean': False,
                'threat_name': None,
                'error': str(e)
            }
```

---

## SQL Injection Prevention

### Django ORM Best Practices

```python
# SAFE: Django ORM automatically escapes queries
petitions = Petition.objects.filter(category=category_name)

# SAFE: Parameterized queries
petitions = Petition.objects.raw(
    'SELECT * FROM petition WHERE category = %s',
    [category_name]
)

# UNSAFE: String interpolation (DON'T DO THIS)
# petitions = Petition.objects.raw(
#     f'SELECT * FROM petition WHERE category = "{category_name}"'
# )

# SAFE: QuerySet methods
search_results = Petition.objects.filter(
    title__icontains=query
)

# For complex queries, use Q objects
from django.db.models import Q

results = Petition.objects.filter(
    Q(title__icontains=query) | Q(description__icontains=query)
)
```

---

## XSS and CSRF Protection

### XSS Prevention

```python
# Django templates auto-escape by default

# SAFE: Automatic escaping
{{ petition.title }}  # <script> becomes &lt;script&gt;

# SAFE: Explicit escaping
{% load static %}
{{ petition.description|escape }}

# UNSAFE: Disable escaping (only for trusted content)
# {{ petition.html_content|safe }}

# For user-generated content, use bleach
from django.utils.safestring import mark_safe
import bleach

def render_description(description):
    cleaned = bleach.clean(description, tags=[], strip=True)
    return mark_safe(cleaned)
```

### CSRF Protection

```python
# All POST forms must include CSRF token

# Template
{% csrf_token %}

# AJAX requests
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

fetch('/api/petition/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
});
```

---

## Secure CPF Storage

### Hashing Strategy

```python
# pressionaapp/utils/crypto.py

import hashlib
from django.conf import settings


class CPFHasher:
    """
    Hash CPF for secure storage.
    
    LGPD Art. 46: Security measures for sensitive personal data.
    """
    
    @staticmethod
    def hash_cpf(cpf_clean):
        """
        Hash CPF using SHA-256 with salt.
        
        Args:
            cpf_clean: CPF without formatting (11 digits)
        
        Returns:
            str: Hexadecimal hash (64 characters)
        """
        # Use secret key as salt
        salt = settings.SECRET_KEY.encode('utf-8')
        cpf_bytes = cpf_clean.encode('utf-8')
        
        # SHA-256 hash
        hasher = hashlib.sha256()
        hasher.update(salt)
        hasher.update(cpf_bytes)
        
        return hasher.hexdigest()
    
    @staticmethod
    def verify_cpf(cpf_clean, cpf_hash):
        """
        Verify CPF against stored hash.
        
        Args:
            cpf_clean: CPF to verify
            cpf_hash: Stored hash
        
        Returns:
            bool: True if match
        """
        computed_hash = CPFHasher.hash_cpf(cpf_clean)
        return computed_hash == cpf_hash


# Usage in models
from pressionaapp.utils.crypto import CPFHasher

# Store
cpf_clean = validate_cpf(form_data['cpf'])
signature.cpf_hash = CPFHasher.hash_cpf(cpf_clean)

# Verify
if CPFHasher.verify_cpf(cpf_input, signature.cpf_hash):
    # CPF matches
    pass
```

---

## API Security

### API Authentication

```python
# For future API endpoints

# pressiona/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}
```

---

## Logging and Monitoring

### Security Event Logging

```python
# pressiona/settings.py

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
        'file_security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['file_security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pressionaapp': {
            'handlers': ['file_security', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Security Events to Log

```python
# pressionaapp/utils/security_logger.py

import logging

security_logger = logging.getLogger('security')


def log_suspicious_activity(event_type, details, request=None):
    """
    Log security events.
    
    Events:
    - Invalid file upload
    - Failed verification
    - Rate limit exceeded
    - Malware detected
    - SQL injection attempt
    - XSS attempt
    """
    ip = get_client_ip(request) if request else 'unknown'
    user = request.user.username if request and request.user.is_authenticated else 'anonymous'
    
    security_logger.warning(
        f"SECURITY EVENT: {event_type} | User: {user} | IP: {ip} | Details: {details}"
    )


# Usage
log_suspicious_activity(
    'malware_detected',
    f'File: {filename}, Threat: {threat_name}',
    request
)
```

---

## Incident Response Plan

### Incident Types

1. **Data Breach**
   - Unauthorized access to CPF/email data
   - Database compromise

2. **Malware Upload**
   - Malicious PDF uploaded
   - Infected file in S3

3. **DoS/DDoS Attack**
   - Service unavailability
   - Resource exhaustion

4. **Fraudulent Signatures**
   - Fake Gov.br signatures
   - Duplicate CPF abuse

### Response Procedures

**1. Detection**
```
- Monitor logs for anomalies
- Alert on security events
- User reports
```

**2. Containment**
```
- Disable affected accounts
- Block malicious IPs
- Quarantine infected files
- Rate limit aggressive requests
```

**3. Investigation**
```
- Review logs
- Identify scope
- Determine attack vector
- Document findings
```

**4. Remediation**
```
- Patch vulnerabilities
- Remove malware
- Restore from backup if needed
- Strengthen defenses
```

**5. Communication**
```
- Notify affected users (LGPD requirement)
- Report to ANPD if CPF breach
- Update status page
```

**6. Post-Incident**
```
- Document lessons learned
- Update procedures
- Improve monitoring
```

---

## Security Checklist

### Pre-Launch

- [ ] All dependencies updated
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] SQL injection tests passed
- [ ] File upload validation tested
- [ ] Rate limiting configured
- [ ] ClamAV or alternative malware scanner set up
- [ ] Logging configured
- [ ] Backup strategy implemented
- [ ] LGPD compliance reviewed
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Incident response plan documented
- [ ] Security contact published

### Ongoing

- [ ] Weekly dependency updates
- [ ] Monthly security audits
- [ ] Quarterly penetration testing
- [ ] Log review (daily)
- [ ] Backup verification (weekly)
- [ ] LGPD compliance audit (quarterly)
- [ ] User data retention cleanup (monthly)

---

**Document Status:** Complete. Ready for Phase 7: Integration Testing.
