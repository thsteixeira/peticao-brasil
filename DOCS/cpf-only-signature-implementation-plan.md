# Comprehensive Plan: Remove CNPJ Signature Support - Accept Only CPF (Natural Persons)

**Project:** Petição Brasil  
**Document Version:** 1.0  
**Created:** January 28, 2026  
**Status:** Planning  
**Objective:** Restrict platform to accept only CPF (natural person) signatures, excluding CNPJ (legal entity) certificates

---

## Executive Summary

Currently, the platform accepts any ICP-Brasil certificate (Gov.br, e-CPF, e-CNPJ, A1, A3). This plan outlines the necessary changes to restrict signature acceptance to natural persons only (CPF-based certificates), excluding legal entities (CNPJ-based certificates).

---

## Table of Contents

1. [Phase 1: Backend Validation Layer](#phase-1-backend-validation-layer)
2. [Phase 2: User Interface Updates](#phase-2-user-interface-updates)
3. [Phase 3: Documentation Updates](#phase-3-documentation-updates)
4. [Phase 4: Admin Interface](#phase-4-admin-interface)
5. [Phase 5: Testing & Validation](#phase-5-testing--validation)
6. [Phase 6: Error Handling & User Experience](#phase-6-error-handling--user-experience)
7. [Phase 7: Security Considerations](#phase-7-security-considerations)
8. [Phase 8: Monitoring & Analytics](#phase-8-monitoring--analytics)
11. [Implementation Priority Matrix](#implementation-priority-matrix)
12. [Risk Assessment](#risk-assessment)
13. [Success Criteria](#success-criteria)
14. [Timeline](#estimated-timeline)

---

## Phase 1: Backend Validation Layer

### 1.1 Certificate Validation Enhancement

**Location:** `apps/signatures/verification_service.py`

**Current State:** The verification service validates ICP-Brasil certificates without distinguishing between CPF (natural person) and CNPJ (legal entity) certificates.

**Required Changes:**
- Add CPF extraction from certificate OID fields
- Implement CNPJ detection logic using ICP-Brasil OID structure
- Add validation to reject CNPJ certificates during the verification pipeline
- Extract CPF from certificate subject using OID 2.16.76.1.3.1 (CPF field in ICP-Brasil certificates)
- Detect CNPJ using OID 2.16.76.1.3.3 (CNPJ field in ICP-Brasil certificates)
- Add rejection logic when CNPJ OID is present in the certificate

**Implementation Points:**
- Modify the `_extract_certificate_info` method to check for CNPJ OIDs
- Add early rejection in `verify_pdf_signature` method if CNPJ is detected
- Update `verification_notes` to indicate "Certificado CNPJ não aceito - apenas pessoas físicas"
- Ensure the certificate chain validation includes CPF-only checks

**Technical Details:**
```python
# OID Constants for ICP-Brasil
OID_CPF = "2.16.76.1.3.1"  # CPF in certificate
OID_CNPJ = "2.16.76.1.3.3"  # CNPJ in certificate (MUST REJECT)

# Add to verification pipeline:
# 1. Parse certificate extensions
# 2. Check for CNPJ OID presence
# 3. If CNPJ detected -> immediate rejection
# 4. If CPF detected -> continue validation
# 5. Log certificate type for audit
```

---

### 1.2 Form Validation

**Location:** `apps/signatures/forms.py`

**Current State:** The SignatureSubmissionForm only validates CPF format but doesn't cross-check against the certificate type.

**Required Changes:**
- Add server-side validation message for CNPJ detection
- Ensure the form validation fails gracefully if someone attempts to circumvent client-side checks
- Add help text clarification that only natural persons can sign
- Update error messages to be explicit about CPF-only requirement

**Update to CPF field:**
- Help text: "Seu CPF (utilizado no certificado digital). Apenas certificados de pessoa física são aceitos."
- Error message: "Certificados CNPJ não são aceitos. Por favor, utilize um certificado e-CPF ou Gov.br."

---

### 1.3 Model Documentation

**Location:** `apps/signatures/models.py`

**Current State:** Model allows any certificate verification.

**Required Changes:**
- Update model docstrings to specify "Natural persons only (CPF)"
- Add comments in the Signature model explaining CNPJ rejection
- Update the `verified_cpf_from_certificate` field help text to clarify it's for natural persons
- Add data migration notes for future reference

**Updated Docstring:**
```python
"""
A verified signature on a petition.
Signer does NOT need to be a registered user.

IMPORTANT: Only natural persons (CPF) are accepted.
Legal entities (CNPJ) will be automatically rejected.
"""
```

---

### 1.4 Email Notification for Rejections

**Location:** `apps/signatures/tasks.py` (Celery task) and `templates/emails/signature_rejected_cnpj.html`

**Required Implementation:**

**Celery Task Integration:**
```python
# In verify_signature_task (Celery task)
from apps.core.email import send_cnpj_rejection_email

def verify_signature_task(signature_id):
    """
    Asynchronous signature verification task.
    Sends email notification on CNPJ rejection.
    """
    signature = Signature.objects.get(id=signature_id)
    
    # ... existing verification code ...
    
    # After verification
    if verification_result['certificate_type'] == 'CNPJ':
        # Send rejection email
        send_cnpj_rejection_email(
            signature=signature,
            petition=signature.petition,
            certificate_info=verification_result
        )
        
        # Update signature status
        signature.verification_status = 'rejected'
        signature.rejection_reason = verification_result['error']
        signature.save()
```

**Email Service Function:**
```python
# apps/core/email.py
def send_cnpj_rejection_email(signature, petition, certificate_info):
    """
    Send email notification for CNPJ certificate rejection.
    """
    context = {
        'signer_name': signature.signer_name,
        'petition_title': petition.title,
        'petition_url': petition.get_absolute_url(),
        'certificate_issuer': certificate_info.get('issuer'),
        'rejection_date': timezone.now(),
        'help_url': settings.SITE_URL + '/help/how-to-sign/',
    }
    
    send_mail(
        subject='Assinatura Rejeitada - Certificado CNPJ Não Aceito',
        message=render_to_string('emails/signature_rejected_cnpj.txt', context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[signature.contact_email],
        html_message=render_to_string('emails/signature_rejected_cnpj.html', context),
        fail_silently=False,
    )
```

**Email Template:** `templates/emails/signature_rejected_cnpj.html`
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Assinatura Rejeitada - Certificado CNPJ</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #fee; border-left: 4px solid #f44; padding: 20px; margin-bottom: 20px;">
        <h2 style="color: #c00; margin-top: 0;">⚠️ Assinatura Rejeitada</h2>
        <p>Olá {{ signer_name }},</p>
        <p>Sua assinatura para a petição <strong>"{{ petition_title }}"</strong> foi rejeitada automaticamente.</p>
    </div>
    
    <div style="background-color: #fff3cd; padding: 15px; margin-bottom: 20px;">
        <h3 style="margin-top: 0;">Motivo da Rejeição</h3>
        <p>O certificado digital utilizado é de <strong>pessoa jurídica (CNPJ)</strong>.</p>
        <p>Nossa plataforma aceita apenas certificados de <strong>pessoa física (CPF)</strong>.</p>
        <p><small>Emissor do certificado: {{ certificate_issuer }}</small></p>
    </div>
    
    <div style="background-color: #d4edda; padding: 15px; margin-bottom: 20px;">
        <h3 style="margin-top: 0;">✅ Como Resolver</h3>
        <ul>
            <li><strong>Gov.br (GRATUITO - Recomendado):</strong><br>
                Acesse <a href="https://gov.br">gov.br</a>, crie ou ative sua conta e eleve para nível Prata ou Ouro.</li>
            <li><strong>e-CPF:</strong><br>
                Adquira um certificado e-CPF em uma Autoridade Certificadora credenciada.</li>
            <li><strong>Certificado A1/A3 de Pessoa Física:</strong><br>
                Se você possui, use-o no lugar do certificado CNPJ.</li>
        </ul>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 15px; margin-bottom: 20px;">
        <h3 style="margin-top: 0;">📖 Próximos Passos</h3>
        <ol>
            <li>Obtenha um certificado de pessoa física (CPF)</li>
            <li>Acesse a petição: <a href="{{ petition_url }}">{{ petition_title }}</a></li>
            <li>Baixe o PDF novamente</li>
            <li>Assine com seu certificado CPF</li>
            <li>Envie o arquivo assinado</li>
        </ol>
    </div>
    
    <div style="text-align: center; padding: 20px;">
        <a href="{{ help_url }}" 
           style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
            📚 Ver Guia Completo de Assinatura
        </a>
    </div>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    
    <p style="color: #666; font-size: 12px; text-align: center;">
        Esta política garante que cada assinatura represente um cidadão brasileiro<br>
        exercendo seu direito de participação democrática.
    </p>
    
    <p style="color: #666; font-size: 12px; text-align: center;">
        <strong>Petição Brasil</strong><br>
        Data da rejeição: {{ rejection_date|date:"d/m/Y H:i" }}
    </p>
</body>
</html>
```

**Plain Text Version:** `templates/emails/signature_rejected_cnpj.txt`
```
Assinatura Rejeitada - Certificado CNPJ Não Aceito

Olá {{ signer_name }},

Sua assinatura para a petição "{{ petition_title }}" foi rejeitada automaticamente.

═════════════════════════════════════════
MOTIVO DA REJEIÇÃO

O certificado digital utilizado é de PESSOA JURÍDICA (CNPJ).
Nossa plataforma aceita apenas certificados de PESSOA FÍSICA (CPF).

Emissor: {{ certificate_issuer }}

═════════════════════════════════════════
COMO RESOLVER

1. Gov.br (GRATUITO - Recomendado)
   → Acesse https://gov.br
   → Crie ou ative sua conta
   → Eleve para nível Prata ou Ouro

2. e-CPF
   → Adquira certificado e-CPF em uma AC credenciada

3. Certificado A1/A3 de Pessoa Física
   → Use seu certificado CPF

═════════════════════════════════════════
PRÓXIMOS PASSOS

1. Obtenha um certificado de pessoa física (CPF)
2. Acesse a petição: {{ petition_url }}
3. Baixe o PDF novamente
4. Assine com seu certificado CPF
5. Envie o arquivo assinado

═════════════════════════════════════════

Guia de Assinatura: {{ help_url }}

Esta política garante que cada assinatura represente um cidadão
brasileiro exercendo seu direito de participação democrática.

Petição Brasil
Data da rejeição: {{ rejection_date|date:"d/m/Y H:i" }}
```

---

## Phase 2: User Interface Updates

### 2.1 Homepage Messaging

**Location:** `templates/static_pages/home.html`

**Current References Found:**
- Line 19: "gov.br, e-CPF, certificados A1, A3 e mais"
- Line 218: "gov.br, e-CPF, etc."
- Line 248: "gov.br, e-CPF, A1, A3, etc."
- Line 406: "e-CPF ou e-CNPJ" ⚠️ **CRITICAL - needs removal**

**Required Changes:**
- Remove all mentions of "e-CNPJ"
- Update text to explicitly state "apenas para pessoas físicas"
- Replace "e-CPF ou e-CNPJ" with "e-CPF (pessoa física)"
- Add clarification: "Apenas certificados de pessoa física são aceitos"
- Update the feature list to emphasize "Assinatura exclusiva para cidadãos brasileiros (CPF)"

**Updated Messaging Examples:**
- "🔐 **Aceita certificados ICP-Brasil de pessoa física:** Gov.br, e-CPF, certificados A1/A3 de CPF"
- "Assinatura digital ICP-Brasil **para cidadãos** (Gov.br, e-CPF de pessoa física)"
- "Baixe o PDF e assine com seu certificado digital ICP-Brasil **de pessoa física (e-CPF)**"

---

### 2.2 How to Sign Guide

**Location:** `templates/help/how_to_sign.html`

**Current References Found:**
- Line 14: "Gov.br, e-CPF, certificados A1, A3"
- Line 36: "e-CPF - Certificado digital de pessoa física"
- Line 57: "e-CPF ou outro certificado ICP-Brasil"
- Line 317: "Posso usar e-CPF em vez de Gov.br?"
- Line 319: "e-CPF e certificados A1/A3"
- Line 376: "Gov.br, e-CPF ou outro"

**Required Changes:**
- Add prominent warning box at the top: 
  ```html
  <div class="bg-yellow-50 border-l-4 border-yellow-400 p-6 mb-8">
      <h3 class="font-bold text-yellow-800">⚠️ IMPORTANTE: Apenas Pessoas Físicas</h3>
      <p>Esta plataforma aceita APENAS certificados de pessoa física (CPF). 
      Certificados empresariais (e-CNPJ) serão rejeitados automaticamente.</p>
  </div>
  ```
- Remove any ambiguity about accepting company certificates
- Update FAQ section to include: "Por que não aceitamos certificados CNPJ?" with explanation:
  - "Esta plataforma é destinada à participação cívica individual"
  - "Petições públicas representam a voz de cidadãos, não empresas"
  - "Apenas pessoas físicas podem criar e assinar petições"
- Clarify that Gov.br must be at least Silver level (which requires CPF)
- Update all examples to emphasize natural person requirement

**New FAQ Entry:**
```html
<h3>❓ Por que não aceitamos certificados CNPJ?</h3>
<p>Nossa plataforma é dedicada à democracia participativa individual. 
Petições públicas representam a voz de cidadãos brasileiros, não de 
empresas ou organizações. Por isso, aceitamos apenas certificados 
digitais de pessoa física (CPF), como Gov.br, e-CPF e certificados 
A1/A3 de pessoa física.</p>
```

---

### 2.3 About/Terms/Privacy Pages

**Locations:**
- `templates/static_pages/about.html`
- `templates/static_pages/terms.html`
- `templates/static_pages/privacy.html`

**Required Changes:**

**About Page:**
- Add section: "Participação Individual"
  - Explain platform is for citizens, not organizations
  - Clarify only natural persons can participate
  - Provide rationale for CPF-only policy

**Terms of Use:**
- Add clause: "Elegibilidade - Apenas Pessoas Físicas"
  - Platform is restricted to natural persons
  - Legal entities cannot create accounts or sign petitions
  - Violation results in signature rejection

**Privacy Policy:**
- Update data collection section
  - Clarify that only natural person data (CPF) is processed
  - Remove any references to corporate data (CNPJ)
  - Update LGPD compliance section for individual data only

---

## Phase 3: Documentation Updates

### 3.1 README File

**Location:** `README.md`

**Current References:**
- Line 92: "Valor Legal: Evidência criptográfica juridicamente válida"
- References to ICP-Brasil without CPF-only specification

**Required Changes:**
- Update feature list:
  ```markdown
  - ✅ Assinatura digital através do Gov.br (ICP-Brasil) - **Apenas Pessoa Física (CPF)**
  - ✅ Verificação automática de assinaturas digitais **de pessoas físicas**
  - ✅ Validação contra certificados ICP-Brasil **de CPF**
  ```
- Add new bullet point:
  ```markdown
  - ✅ **Restrição CPF:** Validação exclusiva de certificados de pessoa física
  ```
- Update "Principais Funcionalidades" section
- Add note in technical requirements about CPF validation
- Update "Avisos Importantes" section to clarify natural person requirement

---

### 3.2 Legal Documentation

**Locations:**
- `DOCS/legal_docs/incident-response-plan.md`
- `DOCS/legal_docs/designacao-encarregado.md`
- `DOCS/legal_docs/data-mapping-ropa.md`

**Current References:**
- CNPJ field placeholders for organization info

**Required Changes:**

**Incident Response Plan:**
- Remove CNPJ handling procedures
- Update data breach scenarios for natural persons only
- Clarify that platform only processes individual CPF data

**Encarregado Designation:**
- Update to reflect natural person focus
- Remove corporate data handling references

**Data Mapping (ROPA):**
- Update data categories: "CPF only, no CNPJ"
- Clarify legal basis for processing natural person data
- Update data retention policies for individual signatures

---

## Phase 4: Admin Interface

### 4.1 Admin Panel Updates

**Location:** `apps/signatures/admin.py`

**Required Changes:**

**New List Filter:**
```python
class CertificateTypeFilter(admin.SimpleListFilter):
    """Filter signatures by certificate type (CPF/CNPJ)"""
    title = 'Tipo de Certificado'
    parameter_name = 'cert_type'
    
    def lookups(self, request, model_admin):
        return (
            ('cpf', 'CPF (Aceito)'),
            ('cnpj', 'CNPJ (Rejeitado)'),
            ('unknown', 'Desconhecido'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'cnpj':
            return queryset.filter(
                rejection_reason__icontains='CNPJ'
            )
        # Additional logic for CPF filtering
```

**Admin Actions:**
- Add bulk action: "Rejeitar certificados CNPJ em lote"
- Add custom view: "Estatísticas de Rejeição CNPJ"
- Add warning message when viewing CNPJ signatures

**List Display Updates:**
- Add column: `certificate_type` (calculated from certificate_info)
- Add icon indicator for CPF ✓ / CNPJ ✗
- Color-code rejected CNPJ signatures in red

**Fieldset Addition:**
```python
('Tipo de Certificado', {
    'fields': ('certificate_type_display', 'is_cnpj_certificate'),
    'classes': ('collapse',),
    'description': 'Apenas certificados CPF são aceitos'
}),
```

---

## Phase 5: Testing & Validation

### 5.1 Test Cases

**Location:** `tests/`

**New Test File: `tests/test_cnpj_rejection.py`**

**Required Tests:**

1. **Test CNPJ Certificate Detection:**
   ```python
   def test_cnpj_certificate_detected():
       """Verify CNPJ OID is correctly detected in certificate"""
       # Create mock certificate with CNPJ OID
       # Assert detection returns True
   ```

2. **Test CNPJ Certificate Rejection:**
   ```python
   def test_cnpj_signature_rejected():
       """Verify signature with CNPJ cert is rejected"""
       # Upload PDF signed with CNPJ
       # Assert verification_status == 'rejected'
       # Assert rejection_reason contains 'CNPJ'
   ```

3. **Test CPF Certificate Acceptance:**
   ```python
   def test_cpf_signature_accepted():
       """Verify signature with CPF cert is accepted"""
       # Upload PDF signed with CPF
       # Assert verification proceeds normally
   ```

4. **Test Error Messages:**
   ```python
   def test_cnpj_error_message():
       """Verify user-friendly error message for CNPJ"""
       # Attempt CNPJ signature
       # Assert error message is clear and helpful
   ```

5. **Test Form Validation:**
   ```python
   def test_form_cnpj_warning():
       """Verify form displays CNPJ warning"""
       # Render signature submission form
       # Assert warning about CPF-only is visible
   ```

**Files to Update:**
- `tests/test_signature_model.py` - Add CNPJ rejection tests
- `tests/test_forms.py` - Add CPF-only validation tests
- `tests/test_views.py` - Add CNPJ submission flow tests
- `tests/test_custody_service.py` - Verify custody cert mentions CPF-only

**Edge Cases to Test:**
- Certificate with both CPF and CNPJ fields (reject)
- Certificate with neither CPF nor CNPJ (manual review)
- Malformed certificate with invalid OIDs
- Certificate chain with mixed CPF/CNPJ
- Performance impact of additional OID parsing

---

### 5.2 Manual Testing Checklist

**Pre-Deployment Testing:**

- [ ] Upload PDF signed with e-CNPJ certificate
  - [ ] Verify automatic rejection
  - [ ] Check error message clarity
  - [ ] Confirm rejection reason logged
  - [ ] Verify rejection email is sent
  - [ ] Verify email content is clear and helpful

- [ ] Upload PDF signed with e-CPF certificate
  - [ ] Verify normal processing
  - [ ] Check no false positive rejection
  - [ ] Confirm approval flow works

- [ ] Test Gov.br Silver/Gold signatures
  - [ ] Verify CPF detection
  - [ ] Check acceptance flow

- [ ] UI/UX Verification:
  - [ ] Homepage shows CPF-only messaging
  - [ ] How-to-sign guide updated
  - [ ] Submission form has warning
  - [ ] Error page is user-friendly
  - [ ] All CNPJ references removed

- [ ] Documentation Check:
  - [ ] README updated
  - [ ] Technical docs reflect changes
  - [ ] Help pages accurate
  - [ ] FAQ answers CNPJ questions

- [ ] Admin Interface:
  - [ ] CNPJ filter works
  - [ ] Statistics accurate
  - [ ] Bulk actions functional

- [ ] Performance:
  - [ ] OID parsing doesn't slow verification
  - [ ] Database queries optimized
  - [ ] No memory leaks

---

## Phase 6: Error Handling & User Experience

### 6.1 Rejection Flow

**When Rejection Occurs:**
The CNPJ certificate rejection happens during **asynchronous background verification** after the user uploads the signed PDF. The flow is:

1. User downloads the petition PDF
2. User signs it with their certificate (CNPJ) outside the platform
3. User uploads the signed PDF through the form
4. **HTTP request completes immediately** - User sees "processing" confirmation
5. **Background task (Celery)** processes the verification asynchronously
6. Verification service detects CNPJ certificate → rejection
7. Signature record updated with rejection status and reason
8. **Email notification sent** to user with rejection details and next steps
9. User can check status on "My Signatures" page (shows "Rejeitada" with rejection reason)

**Email Notification (Production-Ready):**
Since verification is asynchronous, email notification is essential:
- Background task sends email notification when rejection occurs
- User receives immediate notification without needing to check back
- Email includes clear explanation and next steps
- User can also check status on petition page
- Admin can view rejected signatures in real-time in the admin panel

### 6.2 User-Friendly Error Messages

**Context-Specific Messages:**

**1. Verification Failure Page:**
```html
<div class="bg-red-50 border-l-4 border-red-500 p-6 mb-8">
    <div class="flex items-center mb-4">
        <span class="text-4xl mr-4">⚠️</span>
        <h2 class="text-2xl font-bold text-red-900">
            Certificado CNPJ Detectado
        </h2>
    </div>
    <p class="text-red-800 mb-4">
        O certificado digital utilizado é de <strong>pessoa jurídica (CNPJ)</strong>. 
        Esta plataforma aceita apenas assinaturas de <strong>pessoas físicas (CPF)</strong>.
    </p>
    <div class="bg-white rounded-lg p-4 mb-4">
        <h3 class="font-bold text-gray-900 mb-2">Como Resolver:</h3>
        <ul class="space-y-2 text-gray-700">
            <li>✓ Use sua conta Gov.br (gratuito - nível Prata ou Ouro)</li>
            <li>✓ Utilize um certificado e-CPF</li>
            <li>✓ Use certificado A1/A3 de pessoa física</li>
        </ul>
    </div>
    <a href="{% url 'petitions:how_to_sign' %}" 
       class="bg-blue-600 text-white px-6 py-3 rounded-lg inline-block">
        📖 Ver Guia de Assinatura
    </a>
</div>
```

**2. Form Validation Error:**
```
"❌ Certificado CNPJ não aceito. 
Esta plataforma aceita apenas assinaturas de pessoas físicas. 
Por favor, utilize um certificado Gov.br, e-CPF ou A1/A3 de CPF."
```

**3. Admin Rejection Note:**
```
"REJEIÇÃO AUTOMÁTICA: Certificado CNPJ detectado (OID 2.16.76.1.3.3). 
Política da plataforma: apenas pessoas físicas podem assinar petições. 
Data da rejeição: [TIMESTAMP]"
```

**4. API Error Response:**
```json
{
  "error": "signature_rejected",
  "code": "CNPJ_NOT_ACCEPTED",
  "message": "Certificados CNPJ não são aceitos. Use certificado CPF.",
  "details": {
    "detected_certificate_type": "CNPJ",
    "accepted_types": ["CPF"],
    "help_url": "https://peticaobrasil.com.br/help/how-to-sign"
  }
}
```

---

## Phase 7: Security Considerations

### 7.1 Certificate OID Validation

**Technical Implementation:**

**OID Constants:**
```python
# ICP-Brasil OID Structure
# Reference: DOC-ICP-04 - Requisitos Mínimos para as PC ICP-Brasil

# Natural Person (CPF) - ACCEPTED
OID_CPF = x509.ObjectIdentifier("2.16.76.1.3.1")

# Legal Entity (CNPJ) - REJECTED
OID_CNPJ = x509.ObjectIdentifier("2.16.76.1.3.3")

# Other ICP-Brasil OIDs for reference
OID_PIS_PASEP = x509.ObjectIdentifier("2.16.76.1.3.5")
OID_RG = x509.ObjectIdentifier("2.16.76.1.3.2")
OID_CEI = x509.ObjectIdentifier("2.16.76.1.3.7")
```

**Validation Function:**
```python
def extract_certificate_type(certificate):
    """
    Extract certificate type (CPF or CNPJ) from ICP-Brasil certificate.
    
    Args:
        certificate: x509.Certificate object
        
    Returns:
        tuple: (cert_type, value)
            cert_type: 'CPF', 'CNPJ', or 'UNKNOWN'
            value: The extracted CPF/CNPJ number (or None)
    """
    try:
        # Check Subject Alternative Name extension
        san_ext = certificate.extensions.get_extension_for_oid(
            x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )
        
        # Parse Other Name entries
        for name in san_ext.value:
            if isinstance(name, x509.OtherName):
                # Check for CNPJ (MUST REJECT)
                if name.type_id == OID_CNPJ:
                    cnpj_value = name.value.decode('utf-8')
                    return ('CNPJ', cnpj_value)
                
                # Check for CPF (ACCEPTED)
                elif name.type_id == OID_CPF:
                    cpf_value = name.value.decode('utf-8')
                    return ('CPF', cpf_value)
        
        # Fallback: check certificate Subject
        subject = certificate.subject
        # Additional logic for Subject DN parsing
        
        return ('UNKNOWN', None)
        
    except Exception as e:
        logger.error(f"Error extracting certificate type: {e}")
        return ('UNKNOWN', None)
```

**Integration in Verification Service:**
```python
def verify_pdf_signature(self, pdf_file, petition):
    """Enhanced with CPF-only validation"""
    
    # ... existing code ...
    
    # STEP: Certificate Type Validation (ADD THIS)
    cert_type, cert_value = extract_certificate_type(certificate)
    
    if cert_type == 'CNPJ':
        result['verified'] = False
        result['error'] = (
            'Certificado CNPJ detectado. Esta plataforma aceita '
            'apenas certificados de pessoa física (CPF).'
        )
        result['certificate_type'] = 'CNPJ'
        result['rejection_code'] = 'CNPJ_NOT_ACCEPTED'
        
        # Log for audit
        logger.warning(
            f"CNPJ certificate rejected: {cert_value}",
            extra={
                'certificate_serial': certificate.serial_number,
                'petition_id': petition.id,
                'rejection_reason': 'CNPJ_NOT_ACCEPTED'
            }
        )
        
        return result
    
    elif cert_type == 'CPF':
        # Store CPF for later validation
        result['extracted_cpf'] = cert_value
        result['certificate_type'] = 'CPF'
        # Continue normal verification
    
    else:
        # Unknown certificate type - send to manual review
        result['verified'] = False
        result['error'] = 'Tipo de certificado não identificado'
        result['requires_manual_review'] = True
        return result
    
    # ... continue with existing verification ...
```

---

### 7.2 Circumvention Prevention

**Security Measures:**

**1. Server-Side Validation (Never Trust Client)**
- All certificate parsing done server-side
- Client-side warnings are UX only, not security
- Never accept certificate type from user input

**2. OID Parsing Validation**
```python
# Defensive programming
def safe_oid_parse(certificate):
    """Safely parse OIDs with fallback"""
    try:
        cert_type, value = extract_certificate_type(certificate)
        
        # Double-check: if CNPJ found anywhere, reject
        cert_text = certificate.subject.rfc4514_string()
        if 'CNPJ' in cert_text.upper():
            return ('CNPJ', None)
        
        # Cross-validate with issuer
        issuer_text = certificate.issuer.rfc4514_string()
        if 'CNPJ' in issuer_text.upper():
            return ('CNPJ', None)
        
        return (cert_type, value)
        
    except Exception as e:
        # On error, be conservative: manual review
        logger.error(f"OID parsing error: {e}")
        return ('UNKNOWN', None)
```

**3. CPF Format Validation**
```python
# Validate extracted CPF matches expected format
def validate_extracted_cpf(cpf_from_cert, cpf_from_form):
    """
    Cross-validate CPF from certificate vs form submission
    """
    # Normalize both
    cert_cpf = re.sub(r'\D', '', cpf_from_cert)
    form_cpf = re.sub(r'\D', '', cpf_from_form)
    
    # Must match exactly
    if cert_cpf != form_cpf:
        raise ValidationError(
            'CPF do certificado não corresponde ao CPF informado'
        )
    
    # Validate CPF format
    if len(cert_cpf) != 11:
        raise ValidationError('CPF inválido no certificado')
    
    return True
```

**4. Rate Limiting**
```python
# Enhanced rate limiting for signature submissions
@method_decorator(rate_limit(max_requests=5, window=3600), name='post')
class SignatureSubmitView(CreateView):
    """
    Reduced from 10 to 5 attempts per hour to prevent
    brute-force CNPJ circumvention attempts
    """
```

**5. Anomaly Detection**
```python
# Flag suspicious patterns
def detect_anomalies(signature):
    """Detect suspicious signature patterns"""
    
    # Same IP attempting multiple certificate types
    ip_hash = signature.ip_address_hash
    recent_attempts = Signature.objects.filter(
        ip_address_hash=ip_hash,
        created_at__gte=timezone.now() - timedelta(hours=24)
    )
    
    if recent_attempts.count() > 10:
        # Alert admin
        send_security_alert(
            'Suspicious signature activity',
            f'IP {ip_hash[:16]}... made {recent_attempts.count()} attempts'
        )
    
    # Multiple CNPJ rejections from same user
    cnpj_rejections = recent_attempts.filter(
        rejection_reason__icontains='CNPJ'
    ).count()
    
    if cnpj_rejections >= 3:
        # Possible circumvention attempt
        logger.warning(f'Multiple CNPJ attempts from IP {ip_hash[:16]}...')
```

**6. Audit Logging**
```python
# Comprehensive logging for security audit
def log_certificate_check(certificate, result):
    """Log all certificate validations for audit"""
    
    StructuredLogger.log({
        'event': 'certificate_validation',
        'certificate_serial': str(certificate.serial_number),
        'certificate_type': result.get('certificate_type'),
        'issuer': certificate.issuer.rfc4514_string(),
        'subject': certificate.subject.rfc4514_string(),
        'validation_result': result.get('verified'),
        'rejection_reason': result.get('error'),
        'timestamp': timezone.now().isoformat(),
        'oids_found': list(result.get('oids', [])),
    })
```

---

## Phase 8: Monitoring & Analytics

### 8.1 Basic Logging

**Location:** `apps/core/logging_utils.py`

**Logging Functions:**

```python
def log_cnpj_rejection(signature_id, certificate_info, ip_hash):
    """Log CNPJ rejection event for debugging"""
    
    logger.warning(
        "CNPJ certificate rejected",
        extra={
            'event_type': 'cnpj_rejection',
            'signature_id': signature_id,
            'certificate_serial': certificate_info.get('serial_number'),
            'certificate_issuer': certificate_info.get('issuer'),
            'timestamp': timezone.now().isoformat(),
        }
    )


def log_certificate_type_detection(cert_type, petition_id):
    """Log certificate type detection"""
    
    logger.info(
        f"Certificate type detected: {cert_type}",
        extra={
            'event_type': 'certificate_type_detection',
            'certificate_type': cert_type,
            'petition_id': petition_id,
            'timestamp': timezone.now().isoformat(),
        }
    )
```

**Purpose:**
- Track CNPJ rejections for debugging and testing
- Monitor certificate type detection accuracy during development
- Provide audit trail for certificate validation

---

## Implementation Priority Matrix

### Critical Path (Week 1 - Must Do First)

| Task | File(s) | Priority | Est. Time | Dependencies |
|------|---------|----------|-----------|--------------|
| Add OID constants | `verification_service.py` | P0 | 1h | None |
| Implement CNPJ detection | `verification_service.py` | P0 | 3h | OID constants |
| Add rejection logic | `verification_service.py` | P0 | 2h | CNPJ detection |
| Email notification function | `core/email.py` | P0 | 2h | None |
| Email templates (HTML + TXT) | `templates/emails/` | P0 | 2h | None |
| Integrate email in Celery task | `tasks.py` | P0 | 1h | Email function |
| Form validation update | `forms.py` | P0 | 1h | None |
| Add warning to submit page | `signature_submit.html` | P0 | 2h | None |
| Error message template | `templates/errors/` | P0 | 1h | None |
| Write basic tests | `tests/test_cnpj_rejection.py` | P0 | 4h | Backend changes |

**Total: ~19 hours**

---

### High Priority (Week 2 - Do Next)

| Task | File(s) | Priority | Est. Time | Dependencies |
|------|---------|----------|-----------|--------------|
| Update homepage | `home.html` | P1 | 2h | None |
| Update how-to guide | `how_to_sign.html` | P1 | 3h | None |
| README updates | `README.md` | P1 | 1h | None |
| Tech docs update | `DOCS/archive/*.md` | P1 | 4h | None |
| Comprehensive tests | `tests/*.py` | P1 | 6h | Backend complete |
| Manual testing | All | P1 | 4h | Tests written |
| Logging enhancements | `logging_utils.py` | P1 | 2h | None |

**Total: ~22 hours**

---

### Medium Priority (Week 3 - Important)

| Task | File(s) | Priority | Est. Time | Dependencies |
|------|---------|----------|-----------|--------------|
| Admin interface | `admin.py` | P2 | 4h | Backend complete |
| Terms/Privacy update | `static_pages/*.html` | P2 | 2h | None |
| FAQ entries | `help/*.html` | P2 | 2h | None |
| Migration file | `migrations/*.py` | P2 | 2h | None |

**Total: ~10 hours**

---

### Low Priority (Week 4+ - Nice to Have)

| Task | File(s) | Priority | Est. Time | Dependencies |
|------|---------|----------|-----------|--------------|
| Historical data audit | Database | P3 | 4h | None |
| Performance optimization | Various | P3 | 4h | Implementation done |
| Documentation polish | All docs | P3 | 3h | Content complete |

**Total: ~11 hours**

---

**Grand Total Estimated Time: ~62 hours (~2 weeks full-time)**

---

## Risk Assessment

### High Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **False positives (CPF rejected)** | Low (15%) | Critical | • Extensive testing<br>• Conservative OID parsing<br>• Manual review fallback |

---

### Medium Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Certificate parsing errors** | Medium (30%) | Medium | • Defensive programming<br>• Try-catch blocks<br>• Fallback to manual review |
| **Performance degradation** | Low (20%) | Medium | • Performance testing<br>• Optimize OID parsing<br>• Caching where appropriate |
| **Edge cases in certificate formats** | Medium (35%) | Low | • Test diverse certificates<br>• Handle unknown formats gracefully |
| **Incomplete CNPJ detection** | Low (15%) | High | • Multiple detection methods<br>• Cross-validation<br>• Audit logging |

---

### Low Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Legal compliance issues** | Low (10%) | High | • Legal review before deployment<br>• LGPD specialist consultation |
| **Database migration problems** | Low (10%) | Low | • Test migrations in staging<br>• Backup before deployment |
| **Documentation out of sync** | Medium (40%) | Low | • Systematic doc review<br>• Checklist verification |

---

### Risk Mitigation Checklist

**Pre-Deployment:**
- [ ] All tests passing
- [ ] Local testing with sample certificates
- [ ] Documentation reviewed
- [ ] Backup plan ready

**Post-Deployment:**
- [ ] Monitor logs for errors
- [ ] Test with real certificates if available
- [ ] False positive investigation
- [ ] Documentation updates based on testing

---

## Success Criteria

The implementation will be considered **successful** when ALL of the following criteria are met:

### Technical Success Criteria

✅ **Detection Accuracy**
- 100% of CNPJ certificates are detected correctly
- 0% false positives (CPF certificates incorrectly rejected as CNPJ)
- < 1% unknown certificate types requiring manual review

✅ **Performance**
- Certificate type detection adds < 100ms to verification time
- No memory leaks or resource exhaustion
- Database query performance impact < 5%
- 99.9% uptime during rollout

✅ **Security**
- No circumvention methods discovered
- All certificate validations server-side
- Comprehensive audit logging implemented
- Zero security vulnerabilities introduced

✅ **Code Quality**
- 90%+ test coverage on new code
- All tests passing
- Code review completed
- Documentation complete

---

### Development Success Criteria

✅ **Basic Validation**
- Error messages are clear and helpful
- Documentation is accurate
- Implementation works as expected during testing

---

## Estimated Timeline

### Week 1: Backend Implementation
**Days 1-2: Core Logic**
- Implement OID constants and detection logic
- Add CNPJ rejection in verification service
- Create unit tests for detection

**Days 3-4: Integration**
- Integrate detection into verification pipeline
- Add error handling and logging
- Form validation updates

**Day 5: Testing**
- Run full test suite
- Manual testing with sample certificates
- Fix bugs and edge cases

**Deliverables:**
- ✅ CNPJ detection working
- ✅ Email notification system implemented
- ✅ Tests passing
- ✅ Backend ready for UI integration

---

### Week 2: User Interface & Documentation
**Days 1-2: UI Updates**
- Update homepage messaging
- Modify signature submission form
- Add error page templates
- Update help guide

**Days 3-4: Documentation**
- Update README
- Revise technical docs
- Update legal pages (Terms, Privacy)
- Create FAQ entries

**Day 5: Review & Testing**
- Content review
- Accessibility check
- Cross-browser testing
- Documentation completeness check

**Deliverables:**
- ✅ All UI updated with CPF-only messaging
- ✅ Documentation complete and accurate
- ✅ User-facing changes ready

---

### Week 3: Admin & Testing
**Days 1-2: Admin Interface**
- Add admin filters
- Create basic admin views
- Add audit tools

**Days 3-5: Final Testing**
- End-to-end testing
- Admin workflow testing
- Performance testing
- Bug fixes

**Deliverables:**
- ✅ Admin tools functional
- ✅ All tests passing
- ✅ Ready for use

---

### Timeline Summary

```
Week 1: Backend Implementation (5 days)
Week 2: UI & Documentation (5 days)
Week 3: Admin & Testing (5 days)

Total: 15 business days (3 weeks)
```

**Critical Path Items:**
1. Certificate OID detection (Week 1)
2. Verification pipeline integration (Week 1)
3. User-facing error messages (Week 2)

**Parallel Workstreams:**
- Documentation can proceed alongside backend dev
- Admin interface development can overlap with UI work

---

## Post-Implementation Review Checklist

### Initial Testing Review

**Technical Review:**
- [ ] Code quality assessment
- [ ] Security review
- [ ] Performance testing
- [ ] Test coverage review

**Functionality Check:**
- [ ] CNPJ rejection working correctly
- [ ] CPF acceptance working correctly
- [ ] Error messages are clear
- [ ] Documentation is accurate

**Process Improvement:**
- [ ] Document lessons learned
- [ ] Identify optimization opportunities
- [ ] Update documentation gaps

---

## Appendix A: Certificate OID Reference

### ICP-Brasil OID Structure

**Root OID:** 2.16.76.1

**Common OIDs in ICP-Brasil Certificates:**

| OID | Description | Usage | Action |
|-----|-------------|-------|--------|
| 2.16.76.1.3.1 | CPF (Natural Person Tax ID) | Identify individual | ✅ ACCEPT |
| 2.16.76.1.3.3 | CNPJ (Legal Entity Tax ID) | Identify company | ❌ REJECT |
| 2.16.76.1.3.2 | RG (ID Number) | Additional identification | ℹ️ Info only |
| 2.16.76.1.3.5 | PIS/PASEP | Social security number | ℹ️ Info only |
| 2.16.76.1.3.6 | Birth Date | Date of birth | ℹ️ Info only |
| 2.16.76.1.3.7 | CEI (Company ID) | Corporate registration | ❌ REJECT |
| 2.16.76.1.3.8 | Voter ID | Electoral registration | ℹ️ Info only |

**Detection Logic:**
- If OID 2.16.76.1.3.3 (CNPJ) present → REJECT immediately
- If OID 2.16.76.1.3.7 (CEI) present → REJECT (also corporate)
- If OID 2.16.76.1.3.1 (CPF) present → ACCEPT (proceed with validation)
- If neither present → UNKNOWN (manual review)

---

## Appendix B: Testing Checklist

### Unit Tests Checklist

- [ ] `test_detect_cnpj_certificate()`
- [ ] `test_detect_cpf_certificate()`
- [ ] `test_detect_unknown_certificate()`
- [ ] `test_reject_cnpj_signature()`
- [ ] `test_accept_cpf_signature()`
- [ ] `test_cnpj_oid_parsing()`
- [ ] `test_cpf_oid_parsing()`
- [ ] `test_multiple_oid_in_certificate()`
- [ ] `test_malformed_oid()`
- [ ] `test_missing_oid()`
- [ ] `test_form_validation_cnpj_warning()`
- [ ] `test_error_message_generation()`
- [ ] `test_logging_cnpj_rejection()`
- [ ] `test_admin_cnpj_filter()`
- [ ] `test_cnpj_rejection_email_sent()`
- [ ] `test_cnpj_rejection_email_content()`
### Integration Tests Checklist

- [ ] End-to-end CNPJ rejection flow
- [ ] End-to-end CPF acceptance flow
- [ ] Form submission with CNPJ cert
- [ ] PDF verification with CNPJ cert
- [ ] Admin dashboard CNPJ stats
- [ ] Manual review flow for unknown certs
- [ ] Performance with OID parsing

### Manual Testing Checklist

- [ ] Upload PDF signed with e-CNPJ
- [ ] Upload PDF signed with e-CPF
- [ ] Upload PDF signed with Gov.br
- [ ] Upload PDF signed with A1/A3 CPF
- [ ] Verify error message clarity
- [ ] Test admin interface filters
- [ ] Test help documentation links
- [ ] Basic functionality check

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-28 | Implementation Team | Initial comprehensive plan created |

---

## References

1. ICP-Brasil DOC-ICP-04 - Requisitos Mínimos para as PC ICP-Brasil
2. ICP-Brasil DOC-ICP-01 - Políticas de Certificados da ICP-Brasil
3. LGPD (Lei Geral de Proteção de Dados) - Lei 13.709/2018
4. Cryptography library documentation - Certificate parsing
5. Django documentation - Form validation and model constraints
6. Platform existing technical documentation (DOCS/archive/)

---

**END OF DOCUMENT**
