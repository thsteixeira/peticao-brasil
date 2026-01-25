# Security Measures Documentation

**Domain:** peticaobrasil.com.br  
**Last Updated:** January 22, 2026

This document outlines the security measures implemented in the Petição Brasil platform.

## File Upload Security

### 1. File Validation (`apps/core/validators.py`)

**Magic Number Validation:**
- Checks file headers to verify actual file type (not just extension)
- PDF files validated with `%PDF-1.` or `%PDF-2.` magic numbers
- Prevents malicious files disguised with legitimate extensions

**File Size Limits:**
- PDF files: 10 MB maximum
- Image files: 5 MB maximum
- Request body size: 10 MB maximum (enforced by middleware)

**MIME Type Validation:**
- Whitelist-based MIME type checking
- Rejects files with incorrect or missing MIME types
- PDF: `application/pdf` only
- Images: `image/jpeg`, `image/png`, `image/gif`

**Dangerous Content Detection:**
- Scans PDF files for embedded JavaScript (`/JavaScript`, `/JS`)
- Detects launch actions (`/Launch`)
- Identifies potentially malicious forms
- Note: `/AcroForm` allowed as it's required for digital signatures

**Filename Sanitization:**
- Removes path traversal attempts (`../`, `./`)
- Strips special characters and spaces
- Limits filename length to 100 characters
- Normalizes extensions to lowercase

**File Integrity:**
- SHA-256 hash calculation for all uploaded files
- Stored alongside file metadata for later verification
- Prevents file tampering after upload

### 2. Rate Limiting (`django-ratelimit`)

**Signature Submission:**
- Maximum 5 submissions per hour per IP address
- Prevents automated spam attacks
- Protects server resources

**Implementation:**
```python
@method_decorator(ratelimit(key='ip', rate='5/h', method='POST'), name='post')
class SignatureSubmitView(CreateView):
    ...
```

### 3. Security Middleware (`apps/core/middleware.py`)

**SecurityHeadersMiddleware:**
- **Content-Security-Policy (CSP):** Restricts resource loading
  - Scripts: Only from self and TailwindCSS CDN
  - Styles: Only from self and TailwindCSS CDN  
  - Images: Self, data URIs, and HTTPS sources
  - Frames: Blocked (`frame-ancestors 'none'`)
  
- **X-Content-Type-Options:** Set to `nosniff`
  - Prevents MIME type sniffing
  - Forces browser to respect declared content types

- **X-Frame-Options:** Set to `DENY`
  - Prevents clickjacking attacks
  - Blocks page from being loaded in frames/iframes

- **X-XSS-Protection:** Enabled with `1; mode=block`
  - Activates browser's XSS filter
  - Blocks page if XSS attack detected

- **Referrer-Policy:** `strict-origin-when-cross-origin`
  - Controls referrer information sent with requests
  - Protects user privacy

- **Permissions-Policy:** Restricts browser features
  - Disables: geolocation, microphone, camera, payment, USB
  - Reduces attack surface

**FileUploadSecurityMiddleware:**
- Checks total request size before processing
- Rejects requests exceeding 10 MB
- Returns HTTP 403 Forbidden for oversized uploads

### 4. Input Sanitization (`apps/core/security.py`)

**JavaScript Detection:**
- Scans for common XSS patterns:
  - `<script>` tags
  - `javascript:` protocol
  - Event handlers (onclick, onerror, etc.)
  - eval() and expression() functions

**SQL Injection Prevention:**
- Detects common SQL injection patterns
- Blocks suspicious character sequences
- Uses Django ORM for all database queries (parametrized)

**HTML Sanitization (bleach):**
- Allows only safe HTML tags: `<p>`, `<br>`, `<strong>`, `<em>`, `<u>`, `<ol>`, `<ul>`, `<li>`
- Strips all attributes
- Removes all other tags and scripts

### 5. Form-Level Security

**Petition Forms:**
- JavaScript validation on title and description
- HTML sanitization on description field
- Minimum length requirements (10 chars title, 50 chars description)

**Signature Forms:**
- CPF validation with check digit algorithm
- PDF magic number validation
- File hash calculation and storage
- IP address hashing (LGPD compliance)

## Privacy Protection

**Personal Data Hashing:**
- CPF: SHA-256 hash with salting
- IP addresses: SHA-256 hash for tracking without storing PII
- Prevents identification while allowing duplicate detection

**LGPD Compliance:**
- No raw CPF storage
- IP addresses hashed
- File hashes for integrity verification

## Additional Security Features

**CSRF Protection:**
- Django's built-in CSRF middleware enabled
- All forms require CSRF tokens
- Protects against cross-site request forgery

**Session Security:**
- Secure session cookies in production
- HTTPOnly flag prevents JavaScript access
- SameSite policy prevents CSRF

**Database Security:**
- Parametrized queries via Django ORM
- No raw SQL without parameters
- Protection against SQL injection

## Production Recommendations

1. **Enable HTTPS:**
   - Set `SECURE_SSL_REDIRECT = True`
   - Set `SECURE_HSTS_SECONDS = 31536000`
   - Set `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`

2. **Cookie Security:**
   - Set `SESSION_COOKIE_SECURE = True`
   - Set `CSRF_COOKIE_SECURE = True`
   - Set `CSRF_COOKIE_HTTPONLY = True`

3. **Additional Headers:**
   - Consider implementing HSTS preloading
   - Add CAA DNS records for SSL certificates

4. **File Storage:**
   - Use dedicated storage service (S3, CloudFront)
   - Implement virus scanning (ClamAV)
   - Regular backup and integrity checks

5. **Monitoring:**
   - Log all file upload attempts
   - Monitor rate limit violations
   - Alert on suspicious patterns

## Testing Security

Run security checks:
```bash
python manage.py check --deploy
```

Test file uploads:
```bash
# Test oversized file
# Test wrong MIME type
# Test malicious filename
# Test PDF with JavaScript
```

## Security Incident Response

1. **File Upload Attack:**
   - Quarantine uploaded file
   - Block IP address
   - Review logs for pattern
   - Update validation rules

2. **Rate Limit Violation:**
   - Automatic blocking by django-ratelimit
   - Review IP for bot patterns
   - Consider CAPTCHA integration (Step 11)

3. **XSS Attempt:**
   - Blocked by input validation
   - Log attempt details
   - Review form validation
   - Update sanitization rules
