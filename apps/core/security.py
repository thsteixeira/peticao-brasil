"""
Additional security utilities.
"""
import re
from django.core.exceptions import ValidationError


def validate_no_javascript(text):
    """
    Validate that text doesn't contain JavaScript code.
    
    Args:
        text (str): Text to validate
        
    Raises:
        ValidationError: If JavaScript detected
    """
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onload=',
        r'onclick=',
        r'eval\(',
        r'expression\(',
    ]
    
    text_lower = text.lower()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            raise ValidationError(
                'Conteúdo suspeito detectado. Por favor, remova código JavaScript.'
            )
    
    return text


def validate_no_sql_injection(text):
    """
    Basic SQL injection pattern detection.
    
    Args:
        text (str): Text to validate
        
    Raises:
        ValidationError: If SQL injection patterns detected
    """
    sql_patterns = [
        r"('|(\\')|(--)|(-)|(%)|(<)|(>)|(\+)|(\||(\*)|(\()|(\))|(\;))",
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\\))",
        r"((\%27)|(\'))union",
        r"exec(\s|\+)+(s|x)p\w+",
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValidationError(
                'Entrada contém caracteres não permitidos.'
            )
    
    return text


def sanitize_html_input(text):
    """
    Sanitize HTML input by removing tags and dangerous content.
    
    Args:
        text (str): Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    import bleach
    
    # Allow only safe tags
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    allowed_attributes = {}
    
    # Clean the text
    clean_text = bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return clean_text


def check_file_size_limit(file, max_size_mb=10):
    """
    Check if file size is within limit.
    
    Args:
        file: Django UploadedFile object
        max_size_mb (int): Maximum size in megabytes
        
    Returns:
        bool: True if within limit
        
    Raises:
        ValidationError: If file too large
    """
    max_size = max_size_mb * 1024 * 1024
    
    if file.size > max_size:
        raise ValidationError(
            f'Arquivo muito grande. Tamanho máximo: {max_size_mb}MB'
        )
    
    return True
