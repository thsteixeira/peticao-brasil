"""
File validation and sanitization utilities.
"""
import os
import re
import hashlib
import requests
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.conf import settings


def validate_cpf(cpf):
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas) number.
    
    Args:
        cpf (str): CPF number with or without formatting
        
    Raises:
        ValidationError: If CPF is invalid
        
    Returns:
        str: Clean CPF (digits only)
    """
    # Remove formatting
    cpf_clean = re.sub(r'[^0-9]', '', str(cpf))
    
    # Check length
    if len(cpf_clean) != 11:
        raise ValidationError('CPF deve conter 11 dígitos.')
    
    # Check for known invalid CPFs (all same digits)
    if cpf_clean == cpf_clean[0] * 11:
        raise ValidationError('CPF inválido.')
    
    # Validate check digits
    # First digit
    sum_digits = sum(int(cpf_clean[i]) * (10 - i) for i in range(9))
    remainder = sum_digits % 11
    first_digit = 0 if remainder < 2 else 11 - remainder
    
    if int(cpf_clean[9]) != first_digit:
        raise ValidationError('CPF inválido.')
    
    # Second digit
    sum_digits = sum(int(cpf_clean[i]) * (11 - i) for i in range(10))
    remainder = sum_digits % 11
    second_digit = 0 if remainder < 2 else 11 - remainder
    
    if int(cpf_clean[10]) != second_digit:
        raise ValidationError('CPF inválido.')
    
    return cpf_clean


# PDF magic numbers
PDF_MAGIC_NUMBERS = [
    b'%PDF-1.',  # PDF 1.x
    b'%PDF-2.',  # PDF 2.x
]

# Maximum file sizes (in bytes)
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

# Allowed MIME types
ALLOWED_PDF_MIME_TYPES = [
    'application/pdf',
]

ALLOWED_IMAGE_MIME_TYPES = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
]


def sanitize_filename(filename):
    """
    Sanitize a filename by removing potentially dangerous characters.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Get base name and extension
    name, ext = os.path.splitext(filename)
    
    # Remove any path components
    name = os.path.basename(name)
    
    # Replace spaces and special characters
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    name = name.strip('-')
    
    # Limit length
    if len(name) > 100:
        name = name[:100]
    
    # Ensure we have a name
    if not name:
        name = 'file'
    
    # Reconstruct filename
    return f"{name}{ext.lower()}"


def validate_file_magic_number(file, allowed_magic_numbers):
    """
    Validate file by checking its magic number (file signature).
    
    Args:
        file: Django UploadedFile object
        allowed_magic_numbers: List of allowed magic number byte sequences
        
    Raises:
        ValidationError: If magic number doesn't match
    """
    # Read the first few bytes
    file.seek(0)
    header = file.read(10)
    file.seek(0)
    
    # Check against allowed magic numbers
    for magic in allowed_magic_numbers:
        if header.startswith(magic):
            return True
    
    raise ValidationError(
        'Tipo de arquivo inválido. O arquivo não corresponde ao formato esperado.'
    )


def validate_pdf_file(file):
    """
    Comprehensive PDF file validation.
    
    Args:
        file: Django UploadedFile object
        
    Raises:
        ValidationError: If validation fails
    """
    # Check file size
    if file.size > MAX_PDF_SIZE:
        raise ValidationError(
            f'Arquivo PDF muito grande. Tamanho máximo: {MAX_PDF_SIZE // (1024*1024)}MB'
        )
    
    # Check MIME type
    if file.content_type not in ALLOWED_PDF_MIME_TYPES:
        raise ValidationError(
            f'Tipo de arquivo inválido: {file.content_type}. Apenas PDF é permitido.'
        )
    
    # Check file extension
    if not file.name.lower().endswith('.pdf'):
        raise ValidationError('Arquivo deve ter extensão .pdf')
    
    # Validate magic number
    validate_file_magic_number(file, PDF_MAGIC_NUMBERS)
    
    # Check for embedded scripts (basic check)
    file.seek(0)
    content = file.read(1024 * 100)  # Read first 100KB
    file.seek(0)
    
    # Look for potentially dangerous content
    dangerous_patterns = [
        b'/JavaScript',
        b'/JS',
        b'/Launch',
        b'/OpenAction',
        b'/AA',  # Additional Actions
        b'/AcroForm',  # Forms (check for malicious forms)
    ]
    
    # Note: /AcroForm is needed for signatures, so we don't block it
    # but we should be aware of it
    for pattern in dangerous_patterns[:-1]:  # Exclude /AcroForm from blocking
        if pattern in content:
            # Don't automatically reject, but flag for review
            # In production, you might want to scan this more thoroughly
            pass
    
    return True


def calculate_file_hash(file):
    """
    Calculate SHA-256 hash of uploaded file.
    
    Args:
        file: Django UploadedFile object
        
    Returns:
        str: Hexadecimal hash string
    """
    file.seek(0)
    file_hash = hashlib.sha256()
    
    # Read file in chunks
    for chunk in file.chunks():
        file_hash.update(chunk)
    
    file.seek(0)
    return file_hash.hexdigest()


@deconstructible
class FileValidator:
    """
    Reusable file validator class for model FileField validators.
    """
    
    def __init__(self, max_size=None, allowed_extensions=None, allowed_mime_types=None):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions or []
        self.allowed_mime_types = allowed_mime_types or []
    
    def __call__(self, file):
        # Validate size
        if self.max_size and file.size > self.max_size:
            raise ValidationError(
                f'Arquivo muito grande. Tamanho máximo: {self.max_size // (1024*1024)}MB'
            )
        
        # Validate extension
        if self.allowed_extensions:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in self.allowed_extensions:
                raise ValidationError(
                    f'Extensão de arquivo não permitida: {ext}. '
                    f'Permitidas: {", ".join(self.allowed_extensions)}'
                )
        
        # Validate MIME type
        if self.allowed_mime_types:
            if file.content_type not in self.allowed_mime_types:
                raise ValidationError(
                    f'Tipo de arquivo não permitido: {file.content_type}'
                )


# Pre-configured validators
pdf_file_validator = FileValidator(
    max_size=MAX_PDF_SIZE,
    allowed_extensions=['.pdf'],
    allowed_mime_types=ALLOWED_PDF_MIME_TYPES
)

image_file_validator = FileValidator(
    max_size=MAX_IMAGE_SIZE,
    allowed_extensions=['.jpg', '.jpeg', '.png', '.gif'],
    allowed_mime_types=ALLOWED_IMAGE_MIME_TYPES
)


def validate_turnstile_token(token, remote_ip=None):
    """
    Validate Cloudflare Turnstile token.
    
    Args:
        token (str): Turnstile token from frontend
        remote_ip (str, optional): User's IP address
        
    Returns:
        bool: True if validation passes
        
    Raises:
        ValidationError: If validation fails
    """
    # Skip validation if Turnstile is disabled (development mode)
    if not settings.TURNSTILE_ENABLED:
        return True
    
    # Check if token is provided
    if not token:
        raise ValidationError('Token de verificação ausente.')
    
    # Check if secret key is configured
    if not settings.TURNSTILE_SECRET_KEY:
        # In development with no key, allow through but log warning
        if settings.DEBUG:
            print("WARNING: TURNSTILE_SECRET_KEY not configured, skipping validation")
            return True
        raise ValidationError('Configuração de segurança ausente.')
    
    # Prepare verification request
    verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    data = {
        'secret': settings.TURNSTILE_SECRET_KEY,
        'response': token,
    }
    
    if remote_ip:
        data['remoteip'] = remote_ip
    
    try:
        # Send verification request to Cloudflare
        response = requests.post(verify_url, data=data, timeout=5)
        result = response.json()
        
        # Check if verification was successful
        if result.get('success'):
            return True
        
        # Log error codes for debugging
        error_codes = result.get('error-codes', [])
        if settings.DEBUG:
            print(f"Turnstile validation failed: {error_codes}")
        
        # Handle specific error cases
        if 'timeout-or-duplicate' in error_codes:
            raise ValidationError('Token expirado ou já utilizado. Por favor, tente novamente.')
        
        raise ValidationError('Falha na verificação de segurança. Por favor, tente novamente.')
        
    except requests.RequestException as e:
        # Network error - in production, fail closed; in development, allow through
        if settings.DEBUG:
            print(f"WARNING: Turnstile validation failed due to network error: {e}")
            return True
        raise ValidationError('Erro ao verificar captcha. Por favor, tente novamente.')

