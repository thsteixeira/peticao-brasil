# Petição Brasil - Custody Chain Certification Implementation

**Project Phase:** Enhancement - Chain of Custody  
**Document Version:** 1.0  
**Created:** January 23, 2026  
**Status:** Implementation Guide  
**Domain:** peticaobrasil.com.br

---

## Table of Contents

1. [Overview](#overview)
2. [Objectives](#objectives)
3. [Current State Analysis](#current-state-analysis)
4. [Architecture Design](#architecture-design)
5. [Implementation Steps](#implementation-steps)
6. [Data Models](#data-models)
7. [PDF Certificate Generator](#pdf-certificate-generator)
8. [Verification Evidence Structure](#verification-evidence-structure)
9. [Integration Points](#integration-points)
10. [Security Considerations](#security-considerations)
11. [Testing Strategy](#testing-strategy)
12. [Deployment Checklist](#deployment-checklist)

---

## Overview

### Purpose

Create a comprehensive **Custody Chain Certification System** that generates immutable, cryptographically verifiable certificates every time a signature is validated. This provides legal evidence, transparency, and non-repudiation for the entire signature verification process.

### Distribution Strategy

The custody chain certificate and signed petition are distributed to users in **three distinct scenarios**:

#### 📧 **Scenario 1: Email to Signer (After Verification)**
**When:** Immediately after signature is approved  
**To:** The person who signed the petition  
**Contains:**
- Confirmation of successful verification
- Link to download custody chain certificate
- Link to download their signed petition PDF
- Verification details (date, certificate info, status)

**Purpose:** Provide the signer with proof of their participation and verification

---

#### 📧 **Scenario 2: Email to Petition Creator (New Signature Notification)**
**When:** Immediately after a signature is approved on their petition  
**To:** The petition creator  
**Contains:**
- Notification of new signature
- Signer information (name/initials, location)
- Link to download the signed petition PDF
- Link to download the custody chain certificate
- Petition progress update (current count/goal)

**Purpose:** Keep creators informed and provide evidence for each signature

---

#### 📦 **Scenario 3: Bulk Download by Creator (On-Demand)**
**When:** Petition creator requests download  
**To:** The petition creator  
**Contains:** ZIP file with:
- All signed petition PDFs (one per signature)
- All custody chain certificates (one per signature)
- CSV manifest with all signature metadata
- README file with instructions

**Purpose:** Provide complete evidence package for legal/archival purposes

---

### What is Chain of Custody?

A chain of custody is a chronological documentation that records the sequence of custody, control, transfer, analysis, and disposition of evidence. In our context, it proves:

- **When** the signature was submitted
- **How** it was verified
- **What** checks were performed
- **Who** signed the document (verified through ICP-Brasil certificate)
- **Where** the verification occurred (system metadata)
- **Why** it was approved/rejected (verification steps)

### Key Benefits

1. **Legal Evidence** - Admissible proof of signature verification
2. **Transparency** - Complete audit trail visible to users
3. **Trust** - Users receive official verification certificate
4. **Non-repudiation** - Cryptographic proof prevents denial
5. **Compliance** - Meets Brazilian digital signature regulations
6. **Audit** - Complete forensic trail for investigations

---

## Objectives

### Primary Goals

1. ✅ **Generate custody certificate PDF** for every approved signature
2. ✅ **Store immutable verification evidence** as structured JSON
3. ✅ **Calculate verification hash** for tamper detection
4. ✅ **Track complete chain of custody** with timestamps
5. ✅ **Deliver certificate to signers** via email and download
6. ✅ **Notify petition creators** when signatures are received (with certificate)
7. ✅ **Enable bulk download** for petition creators (all PDFs + certificates)
8. ✅ **Provide admin access** to view all certificates
9. ✅ **Enable API access** for programmatic certificate retrieval

### Distribution Scenarios

The custody chain certificate is distributed in **three distinct scenarios**:

**Scenario 1: To the Signer (After Signature Verification)**
- Email sent immediately after signature approval
- Contains: Link to custody certificate + signed petition
- Purpose: Proof of participation and verification

**Scenario 2: To the Petition Creator (When Someone Signs)**
- Email sent when a new signature is verified on their petition
- Contains: Link to both signed PDF + custody certificate
- Purpose: Evidence collection and petition progress tracking

**Scenario 3: Bulk Download by Creator (On Demand)**
- ZIP file generated on request by petition creator
- Contains: All signed PDFs + all custody certificates + CSV manifest
- Purpose: Complete evidence package for legal/archival purposes

### Success Criteria

- Certificate generated within 5 seconds of approval
- Certificate contains all verification details
- Certificate is cryptographically verifiable
- Users can download certificate anytime
- Admins can audit all certificates
- System maintains 99.9% certificate generation success rate

---

## Current State Analysis

### Existing Infrastructure

**✅ Already Implemented:**

1. **Digital Signature Verification** (`apps/signatures/verification_service.py`)
   - ICP-Brasil certificate validation
   - PKCS#7 signature extraction
   - Certificate chain verification
   - Content integrity checks

2. **Timestamp Tracking** (`apps/signatures/models.py`)
   - `created_at` - Submission timestamp
   - `signed_at` - Signature creation timestamp (from certificate)
   - `verified_at` - Verification completion timestamp

3. **Certificate Information Storage**
   - `certificate_info` - JSON field with certificate details
   - `certificate_subject` - Certificate subject DN
   - `certificate_issuer` - Certificate issuer DN
   - `certificate_serial` - Certificate serial number

4. **Audit Trail**
   - `ip_address_hash` - Hashed IP for LGPD compliance
   - `user_agent` - Browser information
   - Structured logging via `StructuredLogger`

5. **PDF Generation Service** (`apps/petitions/pdf_service.py`)
   - ReportLab-based PDF generation
   - Professional styling and layout
   - S3 storage integration

6. **Email Notification System** (`apps/core/tasks.py`)
   - Celery-based async email delivery
   - Template-based emails

### Missing Components

**❌ To Be Implemented:**

1. **Custody Certificate PDF Generator**
   - New service: `apps/signatures/custody_service.py`
   - Dedicated PDF template for custody certificates

2. **Enhanced Data Model**
   - New fields in `Signature` model
   - Migration file

3. **Verification Evidence Structure**
   - Standardized JSON schema for verification evidence
   - Step-by-step verification log

4. **Certificate Distribution**
   - Email template for custody certificate
   - Download endpoint

5. **Admin Interface**
   - View custody certificates
   - Regenerate certificates if needed

---

## Architecture Design

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Signature Submission                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Signature Verification Task                    │
│              (apps/signatures/tasks.py)                     │
│                                                             │
│  1. Validate PDF file                                       │
│  2. Extract digital signature                               │
│  3. Verify ICP-Brasil certificate                           │
│  4. Extract CPF from certificate                            │
│  5. Verify content integrity                                │
│  6. Check for duplicates                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │  Approved?   │
              └──────┬───────┘
                     │ YES
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Generate Custody Chain Certificate                 │
│          (NEW: apps/signatures/custody_service.py)          │
│                                                             │
│  1. Collect verification evidence                           │
│  2. Calculate verification hash                             │
│  3. Build custody chain timeline                            │
│  4. Generate certificate PDF                                │
│  5. Upload to S3 storage                                    │
│  6. Store URL and hash in database                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──────────────────────────────────────────┐
                     │                                          │
                     ▼                                          ▼
┌─────────────────────────────────────┐  ┌────────────────────────────────────┐
│   Send Certificate to Signer        │  │ Send Notification to Creator       │
│   (Email with custody cert)          │  │ (Email with signed PDF + cert)     │
│                                      │  │                                    │
│  - Verification confirmation         │  │ - New signature alert              │
│  - Link to custody certificate       │  │ - Signer information               │
│  - Link to signed petition           │  │ - Link to signed PDF               │
│  - Verification details              │  │ - Link to custody certificate      │
└──────────────────────────────────────┘  │ - Petition progress update         │
                                          └────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Bulk Download Available                           │
│           (For Petition Creator)                            │
│                                                             │
│  Creator can download ZIP containing:                       │
│  - All signed PDFs                                          │
│  - All custody certificates                                 │
│  - CSV manifest with all signature details                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Signature Record
    │
    ├─► verification_evidence (JSON)
    │   ├─► verification_steps[]
    │   ├─► certificate_details{}
    │   ├─► file_integrity{}
    │   └─► metadata{}
    │
    ├─► verification_hash (SHA-256)
    │   └─► Hash of verification_evidence
    │
    ├─► chain_of_custody (JSON)
    │   ├─► submitted
    │   ├─► processing_started
    │   ├─► processing_completed
    │   └─► certificate_generated
    │
    └─► custody_certificate_pdf (FileField)
        └─► URL to S3-stored PDF certificate
```

---

## Implementation Steps

### Summary of Distribution Points

| Scenario | Trigger | Recipient | Delivery Method | Content |
|----------|---------|-----------|-----------------|---------|
| **1. Signer Notification** | Signature approved | Person who signed | Email | Custody cert + signed PDF (links) |
| **2. Creator Notification** | Signature approved | Petition creator | Email | Custody cert + signed PDF (links) |
| **3. Bulk Download** | Creator requests | Petition creator | ZIP download | All signed PDFs + all custody certs + manifest |

---

### Step 1: Enhance Signature Model

**File:** `apps/signatures/models.py`

**Action:** Add new fields to store custody chain data

**New Fields:**

```python
# Custody Chain Certificate
custody_certificate_pdf = models.FileField(
    upload_to='signatures/custody_certificates/',
    storage=MediaStorage(),
    blank=True,
    null=True,
    verbose_name="Certificado de Custódia",
    help_text="Certificado PDF da cadeia de custódia"
)

custody_certificate_url = models.URLField(
    max_length=500,
    blank=True,
    verbose_name="URL do Certificado de Custódia",
    help_text="URL do certificado de custódia no S3"
)

# Verification Evidence (immutable record)
verification_evidence = models.JSONField(
    null=True,
    blank=True,
    verbose_name="Evidências de Verificação",
    help_text="Registro completo de todas as etapas de verificação (JSON)"
)

# Verification Hash (tamper detection)
verification_hash = models.CharField(
    max_length=64,
    blank=True,
    verbose_name="Hash de Verificação",
    help_text="SHA-256 hash das evidências de verificação"
)

# Chain of Custody Timeline
chain_of_custody = models.JSONField(
    null=True,
    blank=True,
    verbose_name="Cadeia de Custódia",
    help_text="Timeline completa de eventos (JSON)"
)

# Processing timestamps
processing_started_at = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name="Processamento Iniciado em",
    help_text="Quando a verificação começou"
)

processing_completed_at = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name="Processamento Concluído em",
    help_text="Quando a verificação terminou"
)

certificate_generated_at = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name="Certificado Gerado em",
    help_text="Quando o certificado de custódia foi gerado"
)
```

**Migration Command:**

```bash
python manage.py makemigrations signatures
python manage.py migrate
```

---

### Step 2: Create Custody Certificate PDF Generator

**File:** `apps/signatures/custody_service.py` (NEW)

**Purpose:** Generate professional custody chain certificate PDFs

**Key Functions:**

1. `generate_custody_certificate(signature)` - Main entry point
2. `CustodyCertificatePDFGenerator` - PDF generation class
3. `calculate_verification_hash(evidence)` - Hash calculation
4. `build_verification_evidence(signature, verification_result)` - Evidence builder
5. `build_chain_of_custody(signature)` - Timeline builder

**PDF Structure:**

```
Page 1:
┌─────────────────────────────────────────────────────────┐
│             CERTIFICADO DE CADEIA DE CUSTÓDIA           │
│                    PETIÇÃO BRASIL                       │
│           Plataforma de Petições Públicas               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [LOGO]                           [QR CODE to verify]   │
│                                                         │
│  CERTIFICADO Nº: [signature.uuid]                       │
│  Emitido em: [certificate_generated_at]                 │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  DADOS DA ASSINATURA                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Assinante: [full_name]                                 │
│  CPF (hash): [cpf_hash]                                 │
│  Email: [email]                                         │
│  Localização: [city]/[state]                            │
│                                                         │
│  Petição: [petition.title]                              │
│  UUID da Petição: [petition.uuid]                       │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  CERTIFICADO DIGITAL ICP-BRASIL                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Emissor: [certificate_issuer]                          │
│  Número de Série: [certificate_serial]                  │
│  Assunto: [certificate_subject]                         │
│  Válido de: [not_before] até [not_after]                │
│  Tipo: ICP-Brasil / Gov.br                              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  VERIFICAÇÕES REALIZADAS                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✓ Validação de Arquivo PDF                            │
│  ✓ Extração de Assinatura Digital                       │
│  ✓ Verificação de Certificado ICP-Brasil                │
│  ✓ Validação de Cadeia de Certificados                  │
│  ✓ Verificação de Período de Validade                   │
│  ✓ Extração de CPF do Certificado                       │
│  ✓ Validação de Integridade de Conteúdo                 │
│  ✓ Verificação de UUID da Petição                       │
│  ✓ Verificação de Duplicatas                            │
│  ✓ Análise de Segurança                                 │
│                                                         │
│  Status Final: APROVADA                                 │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  CADEIA DE CUSTÓDIA                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Recebimento do Documento                            │
│     Data/Hora: [created_at]                             │
│     IP (hash): [ip_address_hash]                        │
│     User Agent: [user_agent]                            │
│                                                         │
│  2. Início da Verificação                               │
│     Data/Hora: [processing_started_at]                  │
│     Sistema: Petição Brasil v1.0                        │
│                                                         │
│  3. Processamento Completado                            │
│     Data/Hora: [processing_completed_at]                │
│     Duração: [duration] segundos                        │
│                                                         │
│  4. Aprovação da Assinatura                             │
│     Data/Hora: [verified_at]                            │
│     Verificador: Sistema Automático                     │
│                                                         │
│  5. Geração do Certificado                              │
│     Data/Hora: [certificate_generated_at]               │
│     Versão: 1.0                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  INTEGRIDADE E AUTENTICIDADE                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Hash SHA-256 das Evidências de Verificação:            │
│  [verification_hash]                                    │
│                                                         │
│  Hash SHA-256 do Arquivo Assinado:                      │
│  [file_hash]                                            │
│                                                         │
│  Este hash pode ser utilizado para verificar que        │
│  as evidências não foram alteradas após a emissão       │
│  do certificado.                                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  DECLARAÇÃO DE CONFORMIDADE                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Este certificado atesta que:                           │
│                                                         │
│  1. A assinatura digital foi verificada com sucesso     │
│     utilizando certificado ICP-Brasil válido.           │
│                                                         │
│  2. Todos os procedimentos de segurança foram           │
│     cumpridos conforme especificado em:                 │
│     https://peticaobrasil.com.br/docs/verificacao       │
│                                                         │
│  3. O documento assinado não foi alterado após a        │
│     assinatura digital.                                 │
│                                                         │
│  4. A identidade do signatário foi verificada           │
│     através do certificado digital ICP-Brasil.          │
│                                                         │
│  5. Esta assinatura foi registrada e contabilizada      │
│     para a petição especificada.                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  INFORMAÇÕES ADICIONAIS                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Este certificado foi gerado automaticamente pelo       │
│  sistema Petição Brasil e possui validade jurídica      │
│  como evidência do processo de verificação.             │
│                                                         │
│  Para verificar a autenticidade deste certificado,      │
│  acesse:                                                │
│  https://peticaobrasil.com.br/verificar/[uuid]          │
│                                                         │
│  Ou escaneie o QR Code no topo deste documento.         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Petição Brasil - Plataforma de Petições Públicas       │
│  https://peticaobrasil.com.br                           │
│                                                         │
│  Documento gerado em: [timestamp]                       │
│  Versão do Sistema: 1.0                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation Template:**

```python
"""
Custody Chain Certificate Generation Service
"""
import hashlib
import json
from datetime import datetime
from io import BytesIO
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from config.storage_backends import MediaStorage


class CustodyCertificatePDFGenerator:
    """Generate custody chain certificate PDFs."""
    
    def __init__(self, signature):
        self.signature = signature
        self.buffer = BytesIO()
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Define custom paragraph styles."""
        # Implementation similar to PetitionPDFGenerator
        pass
    
    def generate(self):
        """Generate the PDF certificate."""
        # Implementation
        pass


def build_verification_evidence(signature, verification_result):
    """
    Build comprehensive verification evidence JSON.
    
    Returns structured evidence that can be hashed and stored.
    """
    evidence = {
        "version": "1.0",
        "signature_uuid": str(signature.uuid),
        "petition_uuid": str(signature.petition.uuid),
        "timestamp": timezone.now().isoformat(),
        
        "verification_steps": [
            {
                "step": "file_validation",
                "status": "passed",
                "timestamp": signature.processing_started_at.isoformat(),
                "details": "PDF file validated successfully"
            },
            {
                "step": "signature_extraction",
                "status": "passed",
                "timestamp": signature.processing_started_at.isoformat(),
                "details": "Digital signature extracted from PDF"
            },
            {
                "step": "certificate_validation",
                "status": "passed",
                "timestamp": signature.processing_started_at.isoformat(),
                "details": "ICP-Brasil certificate chain validated",
                "certificate_serial": signature.certificate_serial
            },
            # ... more steps
        ],
        
        "certificate_details": {
            "issuer": signature.certificate_issuer,
            "subject": signature.certificate_subject,
            "serial_number": signature.certificate_serial,
            "not_before": signature.certificate_info.get('not_before'),
            "not_after": signature.certificate_info.get('not_after'),
        },
        
        "file_integrity": {
            "file_hash": signature.file_hash,
            "content_hash": signature.petition.content_hash,
            "uuid_verified": True,
        },
        
        "signer_information": {
            "cpf_hash": signature.cpf_hash,
            "full_name": signature.full_name,
            "email": signature.email,
            "city": signature.city,
            "state": signature.state,
        },
        
        "metadata": {
            "verifier_version": "1.0",
            "system": "Petição Brasil",
            "processing_duration_seconds": (
                signature.processing_completed_at - signature.processing_started_at
            ).total_seconds() if signature.processing_completed_at else None,
        }
    }
    
    return evidence


def calculate_verification_hash(evidence):
    """
    Calculate SHA-256 hash of verification evidence.
    
    This hash can be used to verify that evidence hasn't been tampered with.
    """
    # Serialize to JSON with sorted keys for consistent hashing
    evidence_json = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(evidence_json.encode('utf-8')).hexdigest()


def build_chain_of_custody(signature):
    """
    Build chronological chain of custody timeline.
    """
    chain = {
        "events": [
            {
                "event": "submission",
                "timestamp": signature.created_at.isoformat(),
                "description": "Documento assinado recebido",
                "ip_hash": signature.ip_address_hash,
                "user_agent": signature.user_agent,
            },
            {
                "event": "processing_started",
                "timestamp": signature.processing_started_at.isoformat() if signature.processing_started_at else None,
                "description": "Verificação automática iniciada",
            },
            {
                "event": "processing_completed",
                "timestamp": signature.processing_completed_at.isoformat() if signature.processing_completed_at else None,
                "description": "Verificação automática concluída",
                "status": signature.verification_status,
            },
            {
                "event": "approval",
                "timestamp": signature.verified_at.isoformat() if signature.verified_at else None,
                "description": "Assinatura aprovada e contabilizada",
            },
            {
                "event": "certificate_generation",
                "timestamp": signature.certificate_generated_at.isoformat() if signature.certificate_generated_at else None,
                "description": "Certificado de custódia gerado",
            },
        ]
    }
    
    return chain


def generate_custody_certificate(signature, verification_result=None):
    """
    Main entry point: Generate custody chain certificate for a signature.
    
    Args:
        signature: Signature model instance
        verification_result: Optional dict with verification details
    
    Returns:
        str: URL to the generated certificate PDF
    """
    from apps.core.logging_utils import StructuredLogger
    logger = StructuredLogger(__name__)
    
    try:
        # Build verification evidence
        evidence = build_verification_evidence(signature, verification_result)
        
        # Calculate verification hash
        verification_hash = calculate_verification_hash(evidence)
        
        # Build chain of custody
        custody_chain = build_chain_of_custody(signature)
        
        # Update signature with evidence and hash
        signature.verification_evidence = evidence
        signature.verification_hash = verification_hash
        signature.chain_of_custody = custody_chain
        signature.certificate_generated_at = timezone.now()
        
        # Generate PDF
        generator = CustodyCertificatePDFGenerator(signature)
        pdf_bytes = generator.generate()
        
        # Save to storage
        storage = MediaStorage()
        filename = f"custody_certificate_{signature.uuid}.pdf"
        filepath = f"signatures/custody_certificates/{filename}"
        
        from django.core.files.base import ContentFile
        saved_path = storage.save(filepath, ContentFile(pdf_bytes))
        
        # Get URL
        certificate_url = storage.url(saved_path)
        
        # Update signature
        signature.custody_certificate_url = certificate_url
        signature.save(update_fields=[
            'verification_evidence',
            'verification_hash',
            'chain_of_custody',
            'certificate_generated_at',
            'custody_certificate_url'
        ])
        
        logger.info(
            "Custody certificate generated successfully",
            signature_uuid=str(signature.uuid),
            certificate_url=certificate_url,
            verification_hash=verification_hash
        )
        
        return certificate_url
        
    except Exception as e:
        logger.error(f"Error generating custody certificate: {str(e)}")
        raise
```

---

### Step 3: Create Database Migration

**Command:**

```bash
python manage.py makemigrations signatures -n add_custody_chain_fields
python manage.py migrate
```

**Migration File Preview:**

```python
# Generated migration file
from django.db import migrations, models
import config.storage_backends

class Migration(migrations.Migration):
    dependencies = [
        ('signatures', '0XXX_previous_migration'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='signature',
            name='custody_certificate_pdf',
            field=models.FileField(
                blank=True,
                null=True,
                storage=config.storage_backends.MediaStorage(),
                upload_to='signatures/custody_certificates/',
                verbose_name='Certificado de Custódia'
            ),
        ),
        # ... other fields
    ]
```

---

### Step 4: Integrate into Verification Task

**File:** `apps/signatures/tasks.py`

**Modification:** Update `verify_signature()` task

**Changes:**

```python
from apps.signatures.custody_service import generate_custody_certificate

@shared_task(bind=True, max_retries=3)
def verify_signature(self, signature_id):
    """Async task to verify a signature's digital certificate."""
    start_time = time.time()
    
    try:
        signature = Signature.objects.get(id=signature_id)
        
        # Update status to processing + set timestamp
        signature.verification_status = Signature.STATUS_PROCESSING
        signature.processing_started_at = timezone.now()
        signature.save(update_fields=['verification_status', 'processing_started_at'])
        
        # ... existing verification code ...
        
        if result['verified']:
            # Signature is valid
            signature.verification_status = Signature.STATUS_APPROVED
            signature.verified_at = timezone.now()
            signature.processing_completed_at = timezone.now()
            
            # Store certificate information
            if result['certificate_info']:
                cert_info = result['certificate_info']
                signature.certificate_subject = cert_info.get('subject', '')
                signature.certificate_issuer = cert_info.get('issuer', '')
                signature.certificate_serial = cert_info.get('serial_number', '')
            
            signature.save()
            
            # Increment petition count
            signature.petition.increment_signature_count()
            
            # NEW: Generate custody chain certificate
            try:
                certificate_url = generate_custody_certificate(signature, result)
                logger.info(
                    "Custody certificate generated",
                    signature_uuid=str(signature.uuid),
                    certificate_url=certificate_url
                )
            except Exception as cert_error:
                logger.error(f"Failed to generate custody certificate: {str(cert_error)}")
                # Don't fail the whole verification if certificate generation fails
            
            # Send verification email with certificate
            try:
                from apps.core.tasks import send_signature_verified_notification
                send_signature_verified_notification.delay(signature.id)
            except Exception as e:
                logger.error(f"Failed to queue verification email: {str(e)}")
            
            return {
                'success': True,
                'signature_uuid': str(signature.uuid),
                'status': 'approved',
                'custody_certificate_url': signature.custody_certificate_url
            }
        
        else:
            # Rejection handling (unchanged)
            signature.processing_completed_at = timezone.now()
            # ... existing code ...
```

---

### Step 5: Create Email Templates

#### 5.1 Email to Signer (After Signature Verification)

**File:** `templates/emails/signature_verified_with_certificate.html` (NEW)

**Purpose:** Email template to send custody certificate to the signer

**Template:**

```html
{% extends "emails/base.html" %}

{% block content %}
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #1E40AF; text-align: center;">Assinatura Verificada com Sucesso! ✓</h1>
    
    <p>Olá, <strong>{{ signature.full_name }}</strong>,</p>
    
    <p>Sua assinatura digital na petição "<strong>{{ signature.petition.title }}</strong>" foi <strong>verificada e aprovada</strong> com sucesso!</p>
    
    <div style="background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 15px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1E40AF;">Certificado de Cadeia de Custódia</h3>
        <p>Geramos um certificado oficial que comprova a autenticidade e integridade da sua assinatura digital.</p>
        <p style="text-align: center; margin: 20px 0;">
            <a href="{{ signature.custody_certificate_url }}" 
               style="background-color: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                📄 Baixar Certificado de Custódia
            </a>
        </p>
    </div>
    
    <h3>Detalhes da Verificação:</h3>
    <ul>
        <li><strong>Petição:</strong> {{ signature.petition.title }}</li>
        <li><strong>Assinado em:</strong> {{ signature.signed_at|date:"d/m/Y H:i" }}</li>
        <li><strong>Verificado em:</strong> {{ signature.verified_at|date:"d/m/Y H:i" }}</li>
        <li><strong>Certificado:</strong> {{ signature.certificate_issuer }}</li>
        <li><strong>Status:</strong> <span style="color: #10B981; font-weight: bold;">APROVADA</span></li>
    </ul>
    
    <h3>O que é o Certificado de Custódia?</h3>
    <p>O Certificado de Cadeia de Custódia é um documento que comprova:</p>
    <ul>
        <li>Que sua assinatura digital foi verificada com certificado ICP-Brasil válido</li>
        <li>Que todos os procedimentos de segurança foram cumpridos</li>
        <li>A data e hora exata de cada etapa do processo</li>
        <li>A integridade do documento assinado</li>
    </ul>
    
    <p>Este certificado possui valor legal como evidência do processo de verificação e pode ser utilizado para comprovar sua participação na petição.</p>
    
    <div style="background-color: #F3F4F6; padding: 15px; border-radius: 6px; margin-top: 20px;">
        <h3 style="margin-top: 0;">Próximos Passos:</h3>
        <ol>
            <li>Baixe e guarde seu certificado de custódia</li>
            <li>Acompanhe o progresso da petição</li>
            <li>Compartilhe a petição com outras pessoas</li>
        </ol>
        <p style="text-align: center; margin-top: 20px;">
            <a href="{{ site_url }}/peticoes/{{ signature.petition.uuid }}/" 
               style="color: #3B82F6; text-decoration: none; font-weight: bold;">
                Ver Petição →
            </a>
        </p>
    </div>
    
    <p style="margin-top: 30px; color: #6B7280; font-size: 14px;">
        Obrigado por participar da democracia direta!<br>
        <strong>Equipe Petição Brasil</strong>
    </p>
</div>
{% endblock %}
```

**Email Task for Signer:**

```python
# In apps/core/tasks.py

@shared_task
def send_signature_verified_notification(signature_id):
    """Send verification success email with custody certificate to signer."""
    from apps.signatures.models import Signature
    
    try:
        signature = Signature.objects.select_related('petition').get(id=signature_id)
        
        context = {
            'signature': signature,
            'site_url': settings.SITE_URL,
        }
        
        send_email(
            subject=f'Assinatura Verificada - {signature.petition.title}',
            template_name='emails/signature_verified_with_certificate.html',
            context=context,
            recipient_list=[signature.email],
        )
        
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
```

---

#### 5.2 Email to Petition Creator (When Someone Signs Their Petition)

**File:** `templates/emails/new_signature_notification_creator.html` (NEW)

**Purpose:** Notify petition creator about new signature with custody certificate attached

**Template:**

```html
{% extends "emails/base.html" %}

{% block content %}
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #1E40AF; text-align: center;">Nova Assinatura Recebida! ✓</h1>
    
    <p>Olá, <strong>{{ petition.creator.get_full_name }}</strong>,</p>
    
    <p>Sua petição "<strong>{{ petition.title }}</strong>" recebeu uma nova assinatura verificada!</p>
    
    <div style="background-color: #ECFDF5; border-left: 4px solid #10B981; padding: 15px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #047857;">Detalhes da Assinatura</h3>
        <ul style="margin: 10px 0;">
            <li><strong>Assinante:</strong> {{ signature.display_name }}</li>
            <li><strong>Localização:</strong> {{ signature.city }}/{{ signature.state }}</li>
            <li><strong>Data:</strong> {{ signature.verified_at|date:"d/m/Y H:i" }}</li>
            <li><strong>Status:</strong> <span style="color: #10B981; font-weight: bold;">APROVADA</span></li>
        </ul>
    </div>
    
    <div style="background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 15px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1E40AF;">Documentação</h3>
        <p>Documentos relacionados a esta assinatura:</p>
        
        <p style="text-align: center; margin: 15px 0;">
            <a href="{{ signature.signed_pdf_url }}" 
               style="background-color: #3B82F6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 5px;">
                📄 Petição Assinada
            </a>
            <a href="{{ signature.custody_certificate_url }}" 
               style="background-color: #059669; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 5px;">
                🔒 Certificado de Custódia
            </a>
        </p>
        
        <p style="font-size: 13px; color: #6B7280;">
            <strong>Certificado de Custódia:</strong> Comprova a autenticidade e integridade da assinatura digital através de cadeia de verificação completa.
        </p>
    </div>
    
    <h3>Progresso da Petição:</h3>
    <div style="background-color: #F3F4F6; padding: 15px; border-radius: 6px;">
        <p style="margin: 0;">
            <strong>Total de assinaturas:</strong> {{ petition.signature_count }} / {{ petition.signature_goal }}
        </p>
        <div style="background-color: #E5E7EB; height: 20px; border-radius: 10px; margin: 10px 0;">
            <div style="background-color: #3B82F6; width: {{ progress_percentage }}%; height: 100%; border-radius: 10px;"></div>
        </div>
        <p style="margin: 0; font-size: 14px; color: #6B7280;">
            {{ progress_percentage|floatformat:1 }}% da meta alcançada
        </p>
    </div>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ site_url }}/peticoes/{{ petition.uuid }}/" 
           style="background-color: #1E40AF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
            Ver Petição →
        </a>
        <br><br>
        <a href="{{ site_url }}/peticoes/{{ petition.uuid }}/assinaturas/" 
           style="color: #3B82F6; text-decoration: none; font-weight: bold;">
            Ver Todas as Assinaturas →
        </a>
    </div>
    
    <p style="margin-top: 30px; color: #6B7280; font-size: 14px;">
        Continue compartilhando sua petição para alcançar mais pessoas!<br>
        <strong>Equipe Petição Brasil</strong>
    </p>
</div>
{% endblock %}
```

**Email Task for Petition Creator:**

```python
# In apps/core/tasks.py

@shared_task
def send_new_signature_notification_to_creator(signature_id):
    """Send notification to petition creator when someone signs their petition."""
    from apps.signatures.models import Signature
    
    try:
        signature = Signature.objects.select_related('petition', 'petition__creator').get(id=signature_id)
        petition = signature.petition
        
        # Calculate progress percentage
        progress_percentage = (petition.signature_count / petition.signature_goal * 100) if petition.signature_goal > 0 else 0
        
        context = {
            'signature': signature,
            'petition': petition,
            'progress_percentage': progress_percentage,
            'site_url': settings.SITE_URL,
        }
        
        # Send to petition creator
        creator_email = petition.creator.email
        if creator_email:
            send_email(
                subject=f'Nova assinatura na sua petição: {petition.title}',
                template_name='emails/new_signature_notification_creator.html',
                context=context,
                recipient_list=[creator_email],
            )
            
            logger.info(
                "New signature notification sent to creator",
                petition_uuid=str(petition.uuid),
                signature_uuid=str(signature.uuid),
                creator_email=creator_email
            )
        
    except Exception as e:
        logger.error(f"Error sending creator notification: {str(e)}")
```

**Integration in Verification Task:**

Update `apps/signatures/tasks.py` to trigger both notifications:

```python
# In verify_signature() task, after approval:

# Send verification email to signer
try:
    from apps.core.tasks import send_signature_verified_notification
    send_signature_verified_notification.delay(signature.id)
except Exception as e:
    logger.error(f"Failed to queue verification email: {str(e)}")

# NEW: Send notification to petition creator
try:
    from apps.core.tasks import send_new_signature_notification_to_creator
    send_new_signature_notification_to_creator.delay(signature.id)
except Exception as e:
    logger.error(f"Failed to queue creator notification: {str(e)}")
```

---

---

#### 5.3 Bulk Download for Petition Creator

**Purpose:** Allow petition creators to download all signed documents and custody certificates in one package

**Implementation:** This will be handled in Step 6 with a dedicated download view.

---

### Step 6: Create Download Endpoints

#### 6.1 Individual Certificate Download

**File:** `apps/signatures/urls.py`

**Add URL Pattern:**

```python
from django.urls import path
from . import views

app_name = 'signatures'

urlpatterns = [
    # ... existing URLs ...
    
    path(
        'certificate/<uuid:uuid>/',
        views.DownloadCustodyCertificateView.as_view(),
        name='download_custody_certificate'
    ),
    
    path(
        'verify-certificate/<uuid:uuid>/',
        views.VerifyCustodyCertificateView.as_view(),
        name='verify_custody_certificate'
    ),
]
```

**File:** `apps/petitions/urls.py`

**Add URL for Bulk Download:**

```python
from django.urls import path
from . import views

app_name = 'petitions'

urlpatterns = [
    # ... existing URLs ...
    
    path(
        '<uuid:uuid>/download-all-signatures/',
        views.DownloadAllSignaturesView.as_view(),
        name='download_all_signatures'
    ),
]
```

**File:** `apps/signatures/views.py`

**Add Individual Download View:**

```python
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
import hashlib
import json


class DownloadCustodyCertificateView(View):
    """Allow users to download their custody certificate."""
    
    def get(self, request, uuid):
        """Serve the custody certificate PDF."""
        signature = get_object_or_404(
            Signature.objects.select_related('petition'),
            uuid=uuid,
            verification_status=Signature.STATUS_APPROVED
        )
        
        if not signature.custody_certificate_url:
            return HttpResponse(
                'Certificado de custódia não disponível',
                status=404
            )
        
        # Redirect to S3 URL or serve from storage
        from django.shortcuts import redirect
        return redirect(signature.custody_certificate_url)


class VerifyCustodyCertificateView(View):
    """API endpoint to verify certificate authenticity."""
    
    def get(self, request, uuid):
        """Return certificate verification data."""
        signature = get_object_or_404(
            Signature.objects.select_related('petition'),
            uuid=uuid,
            verification_status=Signature.STATUS_APPROVED
        )
        
        # Recalculate hash to verify integrity
        if signature.verification_evidence:
            evidence_json = json.dumps(
                signature.verification_evidence,
                sort_keys=True,
                ensure_ascii=False
            )
            calculated_hash = hashlib.sha256(
                evidence_json.encode('utf-8')
            ).hexdigest()
            
            integrity_verified = (calculated_hash == signature.verification_hash)
        else:
            integrity_verified = False
        
        return JsonResponse({
            'signature_uuid': str(signature.uuid),
            'petition_title': signature.petition.title,
            'signer_name': signature.full_name,
            'verified_at': signature.verified_at.isoformat() if signature.verified_at else None,
            'verification_hash': signature.verification_hash,
            'integrity_verified': integrity_verified,
            'certificate_url': signature.custody_certificate_url,
            'status': 'valid' if integrity_verified else 'integrity_check_failed',
        })
```

---

#### 6.2 Bulk Download for Petition Creator

**File:** `apps/petitions/views.py`

**Add Bulk Download View:**

```python
import zipfile
from io import BytesIO
import requests
from django.http import HttpResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from apps.core.logging_utils import StructuredLogger

logger = StructuredLogger(__name__)


class DownloadAllSignaturesView(LoginRequiredMixin, View):
    """
    Allow petition creator to download all signed PDFs and custody certificates.
    Creates a ZIP file containing:
    - All signed petition PDFs
    - All custody chain certificates
    - A CSV manifest with signature details
    """
    
    def get(self, request, uuid):
        """Generate and download ZIP file with all signatures."""
        from apps.petitions.models import Petition
        from apps.signatures.models import Signature
        
        # Get petition
        petition = get_object_or_404(Petition, uuid=uuid)
        
        # Check permission - only creator can download
        if petition.creator != request.user:
            raise PermissionDenied("Apenas o criador da petição pode baixar todas as assinaturas.")
        
        # Get all approved signatures
        signatures = Signature.objects.filter(
            petition=petition,
            verification_status=Signature.STATUS_APPROVED
        ).select_related('petition').order_by('verified_at')
        
        if not signatures.exists():
            return HttpResponse(
                'Nenhuma assinatura aprovada encontrada.',
                status=404
            )
        
        logger.info(
            "Bulk download initiated",
            petition_uuid=str(petition.uuid),
            signature_count=signatures.count(),
            user_id=request.user.id
        )
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add manifest CSV
            manifest_csv = self._generate_manifest_csv(signatures)
            zip_file.writestr('MANIFEST.csv', manifest_csv)
            
            # Add README
            readme_content = self._generate_readme(petition, signatures.count())
            zip_file.writestr('README.txt', readme_content)
            
            # Process each signature
            for idx, signature in enumerate(signatures, 1):
                try:
                    # Download signed PDF
                    if signature.signed_pdf_url:
                        signed_pdf_name = f"{idx:04d}_signed_{signature.uuid}.pdf"
                        signed_pdf_data = self._download_file(signature.signed_pdf_url)
                        if signed_pdf_data:
                            zip_file.writestr(
                                f"signed_pdfs/{signed_pdf_name}",
                                signed_pdf_data
                            )
                    
                    # Download custody certificate
                    if signature.custody_certificate_url:
                        cert_name = f"{idx:04d}_custody_{signature.uuid}.pdf"
                        cert_data = self._download_file(signature.custody_certificate_url)
                        if cert_data:
                            zip_file.writestr(
                                f"custody_certificates/{cert_name}",
                                cert_data
                            )
                    
                except Exception as e:
                    logger.error(
                        f"Error adding signature {signature.uuid} to ZIP: {str(e)}"
                    )
                    # Add error note to manifest but continue
                    error_note = f"Erro ao processar assinatura {signature.uuid}: {str(e)}\n"
                    zip_file.writestr(
                        f"errors/{signature.uuid}.txt",
                        error_note
                    )
        
        # Prepare response
        zip_buffer.seek(0)
        
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        filename = f"assinaturas_{petition.uuid}.zip"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(
            "Bulk download completed",
            petition_uuid=str(petition.uuid),
            user_id=request.user.id,
            zip_size_bytes=len(zip_buffer.getvalue())
        )
        
        return response
    
    def _download_file(self, url):
        """Download file from URL and return bytes."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {str(e)}")
            return None
    
    def _generate_manifest_csv(self, signatures):
        """Generate CSV manifest of all signatures."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Número',
            'UUID da Assinatura',
            'Nome Completo',
            'Email',
            'Cidade',
            'Estado',
            'Data de Assinatura',
            'Data de Verificação',
            'Status',
            'Emissor do Certificado',
            'Número de Série',
            'Hash de Verificação',
            'URL PDF Assinado',
            'URL Certificado de Custódia'
        ])
        
        # Data rows
        for idx, sig in enumerate(signatures, 1):
            writer.writerow([
                idx,
                str(sig.uuid),
                sig.full_name,
                sig.email,
                sig.city,
                sig.state,
                sig.signed_at.strftime('%d/%m/%Y %H:%M:%S') if sig.signed_at else '',
                sig.verified_at.strftime('%d/%m/%Y %H:%M:%S') if sig.verified_at else '',
                sig.get_verification_status_display(),
                sig.certificate_issuer,
                sig.certificate_serial,
                sig.verification_hash or '',
                sig.signed_pdf_url or '',
                sig.custody_certificate_url or ''
            ])
        
        return output.getvalue()
    
    def _generate_readme(self, petition, signature_count):
        """Generate README file for the ZIP package."""
        return f"""
PETIÇÃO BRASIL - PACOTE DE ASSINATURAS
========================================

Petição: {petition.title}
UUID: {petition.uuid}
Data de Download: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
Total de Assinaturas: {signature_count}

CONTEÚDO DESTE ARQUIVO
----------------------

1. MANIFEST.csv
   Planilha com todas as assinaturas e metadados

2. signed_pdfs/
   PDFs da petição assinados digitalmente pelos signatários

3. custody_certificates/
   Certificados de cadeia de custódia para cada assinatura

4. README.txt
   Este arquivo

SOBRE OS CERTIFICADOS DE CUSTÓDIA
----------------------------------

Cada assinatura possui um Certificado de Cadeia de Custódia que comprova:

- A verificação da assinatura digital ICP-Brasil
- A integridade do documento assinado
- A cronologia completa do processo de verificação
- O hash de verificação para detecção de adulteração

VERIFICAÇÃO DE AUTENTICIDADE
-----------------------------

Para verificar a autenticidade de qualquer certificado:

1. Acesse: https://peticaobrasil.com.br/assinaturas/verify-certificate/[UUID]
2. Compare o hash de verificação retornado com o hash no certificado
3. Se os hashes coincidirem, o certificado é autêntico e não foi alterado

IMPORTANTE
----------

- Estes documentos possuem valor legal como evidência
- Mantenha os arquivos em local seguro
- Não modifique os PDFs, pois isso invalidará as assinaturas digitais
- Os hashes de verificação garantem a integridade dos documentos

Para mais informações:
https://peticaobrasil.com.br

Equipe Petição Brasil
        """.strip()
```

**Template Update for Petition Detail Page:**

Add download button for petition creators in `templates/petitions/petition_detail.html`:

```html
{% if user == petition.creator %}
<div class="creator-actions mt-4">
    <h3>Ações do Criador</h3>
    <a href="{% url 'petitions:download_all_signatures' petition.uuid %}" 
       class="btn btn-primary">
        📦 Baixar Todas as Assinaturas
    </a>
    <p class="text-sm text-gray-600 mt-2">
        Baixa um arquivo ZIP contendo todos os PDFs assinados e certificados de custódia.
    </p>
</div>
{% endif %}
```

---

### Step 7: Update Admin Interface
    def get(self, request, uuid):
        """Serve the custody certificate PDF."""
        signature = get_object_or_404(
            Signature.objects.select_related('petition'),
            uuid=uuid,
            verification_status=Signature.STATUS_APPROVED
        )
        
        if not signature.custody_certificate_url:
            return HttpResponse(
                'Certificado de custódia não disponível',
                status=404
            )
        
        # Redirect to S3 URL or serve from storage
        from django.shortcuts import redirect
        return redirect(signature.custody_certificate_url)


class VerifyCustodyCertificateView(View):
    """API endpoint to verify certificate authenticity."""
    
    def get(self, request, uuid):
        """Return certificate verification data."""
        signature = get_object_or_404(
            Signature.objects.select_related('petition'),
            uuid=uuid,
            verification_status=Signature.STATUS_APPROVED
        )
        
        # Recalculate hash to verify integrity
        if signature.verification_evidence:
            evidence_json = json.dumps(
                signature.verification_evidence,
                sort_keys=True,
                ensure_ascii=False
            )
            calculated_hash = hashlib.sha256(
                evidence_json.encode('utf-8')
            ).hexdigest()
            
            integrity_verified = (calculated_hash == signature.verification_hash)
        else:
            integrity_verified = False
        
        return JsonResponse({
            'signature_uuid': str(signature.uuid),
            'petition_title': signature.petition.title,
            'signer_name': signature.full_name,
            'verified_at': signature.verified_at.isoformat() if signature.verified_at else None,
            'verification_hash': signature.verification_hash,
            'integrity_verified': integrity_verified,
            'certificate_url': signature.custody_certificate_url,
            'status': 'valid' if integrity_verified else 'integrity_check_failed',
        })
```

---

### Step 7: Update Admin Interface

**File:** `apps/signatures/admin.py`

**Enhance Admin:**

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import Signature


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'petition',
        'verification_status',
        'created_at',
        'verified_at',
        'custody_certificate_link',
    ]
    
    list_filter = [
        'verification_status',
        'state',
        'created_at',
        'verified_at',
    ]
    
    search_fields = [
        'full_name',
        'email',
        'petition__title',
        'uuid',
    ]
    
    readonly_fields = [
        'uuid',
        'cpf_hash',
        'ip_address_hash',
        'verification_hash',
        'verification_evidence_display',
        'chain_of_custody_display',
        'custody_certificate_preview',
        'created_at',
        'verified_at',
        'processing_started_at',
        'processing_completed_at',
        'certificate_generated_at',
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'uuid',
                'petition',
                'full_name',
                'email',
                'city',
                'state',
            )
        }),
        ('Verificação', {
            'fields': (
                'verification_status',
                'verified_at',
                'verification_notes',
                'rejection_reason',
            )
        }),
        ('Certificado Digital', {
            'fields': (
                'certificate_subject',
                'certificate_issuer',
                'certificate_serial',
                'verified_cpf_from_certificate',
            )
        }),
        ('Cadeia de Custódia', {
            'fields': (
                'custody_certificate_preview',
                'verification_hash',
                'verification_evidence_display',
                'chain_of_custody_display',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'processing_started_at',
                'processing_completed_at',
                'verified_at',
                'certificate_generated_at',
            )
        }),
        ('Segurança', {
            'fields': (
                'cpf_hash',
                'ip_address_hash',
                'user_agent',
            )
        }),
    )
    
    def custody_certificate_link(self, obj):
        """Display link to custody certificate."""
        if obj.custody_certificate_url:
            return format_html(
                '<a href="{}" target="_blank">📄 Ver Certificado</a>',
                obj.custody_certificate_url
            )
        return '-'
    custody_certificate_link.short_description = 'Certificado'
    
    def custody_certificate_preview(self, obj):
        """Display custody certificate with download link."""
        if obj.custody_certificate_url:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Baixar Certificado de Custódia</a><br>'
                '<small>Hash de Verificação: <code>{}</code></small>',
                obj.custody_certificate_url,
                obj.verification_hash or 'N/A'
            )
        return format_html('<em>Certificado não gerado</em>')
    custody_certificate_preview.short_description = 'Certificado de Custódia'
    
    def verification_evidence_display(self, obj):
        """Display verification evidence as formatted JSON."""
        if obj.verification_evidence:
            import json
            evidence_pretty = json.dumps(obj.verification_evidence, indent=2, ensure_ascii=False)
            return format_html('<pre style="font-size: 11px;">{}</pre>', evidence_pretty)
        return '-'
    verification_evidence_display.short_description = 'Evidências de Verificação'
    
    def chain_of_custody_display(self, obj):
        """Display chain of custody timeline."""
        if obj.chain_of_custody:
            import json
            chain_pretty = json.dumps(obj.chain_of_custody, indent=2, ensure_ascii=False)
            return format_html('<pre style="font-size: 11px;">{}</pre>', chain_pretty)
        return '-'
    chain_of_custody_display.short_description = 'Cadeia de Custódia'
    
    actions = ['regenerate_custody_certificates']
    
    def regenerate_custody_certificates(self, request, queryset):
        """Admin action to regenerate custody certificates."""
        from apps.signatures.custody_service import generate_custody_certificate
        
        count = 0
        for signature in queryset.filter(verification_status=Signature.STATUS_APPROVED):
            try:
                generate_custody_certificate(signature)
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Erro ao regenerar certificado para {signature.uuid}: {str(e)}',
                    level='error'
                )
        
        self.message_user(
            request,
            f'{count} certificado(s) regenerado(s) com sucesso.',
            level='success'
        )
    
    regenerate_custody_certificates.short_description = 'Regenerar certificados de custódia'
```

---

### Step 8: Add QR Code Support (Optional Enhancement)

**Purpose:** Add QR code to certificate for easy verification

**Install Library:**

```bash
pip install qrcode[pil]==7.4.2
```

**Update Requirements:**

```txt
qrcode[pil]==7.4.2
```

**Integration in PDF Generator:**

```python
import qrcode
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

def _generate_qr_code(self, url):
    """Generate QR code for certificate verification."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img
```

---

## Verification Evidence Structure

### Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Verification Evidence",
  "type": "object",
  "required": [
    "version",
    "signature_uuid",
    "petition_uuid",
    "timestamp",
    "verification_steps",
    "certificate_details",
    "file_integrity"
  ],
  "properties": {
    "version": {
      "type": "string",
      "description": "Evidence format version",
      "example": "1.0"
    },
    "signature_uuid": {
      "type": "string",
      "format": "uuid",
      "description": "UUID of the signature"
    },
    "petition_uuid": {
      "type": "string",
      "format": "uuid",
      "description": "UUID of the petition"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "When evidence was generated"
    },
    "verification_steps": {
      "type": "array",
      "description": "All verification steps performed",
      "items": {
        "type": "object",
        "required": ["step", "status", "timestamp"],
        "properties": {
          "step": {
            "type": "string",
            "enum": [
              "file_validation",
              "signature_extraction",
              "certificate_validation",
              "certificate_chain_validation",
              "validity_period_check",
              "cpf_extraction",
              "content_integrity",
              "uuid_verification",
              "duplicate_check",
              "security_scan"
            ]
          },
          "status": {
            "type": "string",
            "enum": ["passed", "failed", "skipped"]
          },
          "timestamp": {
            "type": "string",
            "format": "date-time"
          },
          "details": {
            "type": "string",
            "description": "Additional information about the step"
          }
        }
      }
    },
    "certificate_details": {
      "type": "object",
      "properties": {
        "issuer": {"type": "string"},
        "subject": {"type": "string"},
        "serial_number": {"type": "string"},
        "not_before": {"type": "string", "format": "date-time"},
        "not_after": {"type": "string", "format": "date-time"},
        "signature_algorithm": {"type": "string"}
      }
    },
    "file_integrity": {
      "type": "object",
      "properties": {
        "file_hash": {"type": "string"},
        "content_hash": {"type": "string"},
        "uuid_verified": {"type": "boolean"},
        "file_size_bytes": {"type": "integer"}
      }
    },
    "signer_information": {
      "type": "object",
      "properties": {
        "cpf_hash": {"type": "string"},
        "full_name": {"type": "string"},
        "email": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"}
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "verifier_version": {"type": "string"},
        "system": {"type": "string"},
        "processing_duration_seconds": {"type": "number"},
        "icp_brasil_roots_version": {"type": "string"}
      }
    }
  }
}
```

### Example Evidence Document

```json
{
  "version": "1.0",
  "signature_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "petition_uuid": "f1e2d3c4-b5a6-7890-dcba-fe0987654321",
  "timestamp": "2026-01-23T14:30:45.123456Z",
  
  "verification_steps": [
    {
      "step": "file_validation",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:15.123456Z",
      "details": "PDF file validated successfully - size: 524288 bytes"
    },
    {
      "step": "signature_extraction",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:20.123456Z",
      "details": "PKCS#7 signature extracted from PDF"
    },
    {
      "step": "certificate_validation",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:25.123456Z",
      "details": "ICP-Brasil certificate validated",
      "certificate_serial": "1234567890ABCDEF"
    },
    {
      "step": "certificate_chain_validation",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:30.123456Z",
      "details": "Certificate chain verified against ICP-Brasil roots"
    },
    {
      "step": "validity_period_check",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:32.123456Z",
      "details": "Certificate is within validity period"
    },
    {
      "step": "cpf_extraction",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:35.123456Z",
      "details": "CPF extracted from certificate subject"
    },
    {
      "step": "content_integrity",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:38.123456Z",
      "details": "PDF content hash matches original petition"
    },
    {
      "step": "uuid_verification",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:40.123456Z",
      "details": "Petition UUID verified in signed PDF"
    },
    {
      "step": "duplicate_check",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:42.123456Z",
      "details": "No duplicate signature found for this CPF"
    },
    {
      "step": "security_scan",
      "status": "passed",
      "timestamp": "2026-01-23T14:30:45.123456Z",
      "details": "No security threats detected"
    }
  ],
  
  "certificate_details": {
    "issuer": "CN=Autoridade Certificadora do SERPRO Final SSL,OU=Autoridade Certificadora Raiz Brasileira v10,O=ICP-Brasil,C=BR",
    "subject": "CN=João Silva:12345678900,OU=Certificado PF A3,O=ICP-Brasil,C=BR",
    "serial_number": "1234567890ABCDEF",
    "not_before": "2024-01-15T12:00:00Z",
    "not_after": "2027-01-15T12:00:00Z",
    "signature_algorithm": "sha256WithRSAEncryption"
  },
  
  "file_integrity": {
    "file_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
    "content_hash": "f1e2d3c4b5a6789098765432109876543210fedcba0987654321fedcba098765",
    "uuid_verified": true,
    "file_size_bytes": 524288
  },
  
  "signer_information": {
    "cpf_hash": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "full_name": "João Silva",
    "email": "joao.silva@example.com",
    "city": "São Paulo",
    "state": "SP"
  },
  
  "metadata": {
    "verifier_version": "1.0",
    "system": "Petição Brasil",
    "processing_duration_seconds": 30.5,
    "icp_brasil_roots_version": "2026-01"
  }
}
```

---

## Security Considerations

### 1. Hash Integrity

**Verification Hash Calculation:**
- Use SHA-256 algorithm
- Serialize JSON with sorted keys
- Store hash alongside evidence
- Recalculate on verification to detect tampering

### 2. Immutability

**Ensuring Evidence Cannot Be Modified:**
- Use `JSONField` with database-level constraints
- Never update evidence after generation
- Use read-only fields in admin interface
- Log any attempts to modify evidence

### 3. Storage Security

**S3 Security:**
- Private bucket access
- Signed URLs with expiration
- Encryption at rest (S3 server-side encryption)
- Access logging enabled

### 4. LGPD Compliance

**Privacy Protection:**
- Store CPF as hash only
- Store IP as hash only
- Email is optional and encrypted
- Full name can be hidden with privacy setting
- User can request data deletion

### 5. Audit Trail

**Logging Requirements:**
- Log all certificate generation events
- Log all certificate access events
- Log verification hash mismatches
- Alert on suspicious patterns

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_custody_service.py`

```python
import pytest
from apps.signatures.custody_service import (
    build_verification_evidence,
    calculate_verification_hash,
    build_chain_of_custody,
    generate_custody_certificate,
)
from apps.signatures.models import Signature


@pytest.mark.django_db
class TestCustodyService:
    
    def test_build_verification_evidence(self, approved_signature):
        """Test evidence building."""
        evidence = build_verification_evidence(approved_signature, None)
        
        assert evidence['version'] == '1.0'
        assert evidence['signature_uuid'] == str(approved_signature.uuid)
        assert 'verification_steps' in evidence
        assert len(evidence['verification_steps']) > 0
    
    def test_calculate_verification_hash(self):
        """Test hash calculation is deterministic."""
        evidence = {'test': 'data', 'number': 123}
        
        hash1 = calculate_verification_hash(evidence)
        hash2 = calculate_verification_hash(evidence)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_build_chain_of_custody(self, approved_signature):
        """Test custody chain building."""
        chain = build_chain_of_custody(approved_signature)
        
        assert 'events' in chain
        assert len(chain['events']) > 0
        
        # Check required events
        event_types = [e['event'] for e in chain['events']]
        assert 'submission' in event_types
        assert 'approval' in event_types
    
    def test_generate_custody_certificate(self, approved_signature):
        """Test full certificate generation."""
        certificate_url = generate_custody_certificate(approved_signature)
        
        assert certificate_url is not None
        assert 'custody_certificate' in certificate_url
        
        # Reload signature
        approved_signature.refresh_from_db()
        
        assert approved_signature.verification_hash is not None
        assert approved_signature.verification_evidence is not None
        assert approved_signature.chain_of_custody is not None
        assert approved_signature.custody_certificate_url == certificate_url
```

### Integration Tests

**File:** `tests/test_custody_integration.py`

```python
import pytest
from django.core import mail
from apps.signatures.tasks import verify_signature


@pytest.mark.django_db
class TestCustodyIntegration:
    
    def test_verification_generates_certificate(self, pending_signature):
        """Test that successful verification generates custody certificate."""
        # Trigger verification
        result = verify_signature(pending_signature.id)
        
        # Reload signature
        pending_signature.refresh_from_db()
        
        # Check certificate was generated
        assert pending_signature.custody_certificate_url is not None
        assert pending_signature.verification_hash is not None
        assert pending_signature.certificate_generated_at is not None
    
    def test_certificate_sent_via_email(self, approved_signature):
        """Test that certificate is sent via email."""
        # Check email was sent
        assert len(mail.outbox) > 0
        
        # Check email contains certificate link
        email = mail.outbox[0]
        assert 'certificado de custódia' in email.body.lower()
        assert approved_signature.custody_certificate_url in email.body
```

### End-to-End Tests

**Test Scenarios:**
1. Submit signature → Verify → Certificate generated → Email sent
2. Download certificate via web interface
3. Verify certificate integrity via API
4. Admin regenerates certificate
5. Certificate contains all required information

---

## Deployment Checklist

### Pre-Deployment

- [ ] Add `requests` library to requirements.txt (for bulk download)
- [ ] Create and test database migration
- [ ] Implement `CustodyCertificatePDFGenerator` class
- [ ] Implement `custody_service.py` module
- [ ] Update `verify_signature` task
- [ ] Create email template for signers
- [ ] Create email template for petition creators
- [ ] Add URL patterns for individual and bulk download
- [ ] Implement individual certificate download view
- [ ] Implement bulk download view for creators
- [ ] Add views for download and verification
- [ ] Update admin interface
- [ ] Add download button to petition detail page (for creators)
- [ ] Write unit tests (>80% coverage)
- [ ] Write integration tests
- [ ] Test bulk download with large datasets (100+ signatures)
- [ ] Update documentation

### Deployment Steps

1. **Test in Development:**
   ```bash
   python manage.py test tests.test_custody_service
   python manage.py test tests.test_custody_integration
   ```

2. **Run Migration:**
   ```bash
   # Development
   python manage.py makemigrations signatures
   python manage.py migrate
   
   # Production (Heroku)
   heroku run python manage.py migrate --app peticaobrasil
   ```

3. **Generate Certificates for Existing Signatures:**
   ```bash
   # Django shell
   python manage.py shell
   
   from apps.signatures.models import Signature
   from apps.signatures.custody_service import generate_custody_certificate
   
   # Generate for all approved signatures
   for sig in Signature.objects.filter(
       verification_status='approved',
       custody_certificate_url=''
   ):
       try:
           generate_custody_certificate(sig)
           print(f"✓ {sig.uuid}")
       except Exception as e:
           print(f"✗ {sig.uuid}: {e}")
   ```

4. **Verify S3 Storage:**
   ```bash
   # Check that certificates are being uploaded to S3
   aws s3 ls s3://peticaobrasil-media/signatures/custody_certificates/
   ```

5. **Test Email Delivery:**
   - Submit test signature
   - Verify signer receives certificate email
   - Verify creator receives notification email
   - Test download links in both emails

6. **Test Bulk Download:**
   - Create test petition with multiple signatures
   - Test ZIP generation and download
   - Verify all files are includ for both signer and creator emails
- [ ] Test individual download endpoints
- [ ] Test bulk download functionality
- [ ] Test verification API
- [ ] Monitor ZIP generation performance
- [ ] Check bulk download file sizes
- [ ] Monitor error logs
- [ ] Update user documentation
- [ ] Create help article about custody certificates
- [ ] Create help article about bulk download for creators

- [ ] Monitor certificate generation success rate
- [ ] Check S3 storage usage
- [ ] Verify email delivery  (individual)
- Bulk download count
- Average bulk download size
- Bulk download generation time
- Verification API usage
- Email delivery rate (signer notifications)
- Email delivery rate (creator notifications)oints
- [ ] Test verification API
- [ ] Monitor error logs
- [ ] Update user documentation
- [ ] Announce feature to users

### Monitoring

**Key Metrics:**
- Certificate generation success rate (target: >99%)
- Average generation time (target: <5s)
- S3 storage growth rate
- Certificate download count
- Verification API usage

**Alerts:**
- Certificate generation failure
- Verification hash mismatch
- High generation time (>10s)
- S3 upload failures
- Email delivery failures

---

## Future Enhancements

### Phase 2 Features

1. **Blockchain Integration**
   - Store verification hashes on blockchain
   - Immutable public audit trail
   - Third-party verification

2. **Advanced Analytics**
   - Verification statistics dashboard
   - Certificate download analytics
   - Fraud detection patterns

3. **Certificate Revocation**
   - Revoke certificates if fraud detected
   - Revocation list API
   - Certificate status checking

4. **Multi-Language Support**
   - Generate certificates in multiple languages
   - Internationalization of templates
   - Language preference selection

5. **Enhanced Security**
   - Sign certificates with platform's own ICP-Brasil certificate
   - Timestamping service integration
   - Advanced cryptographic proofs

---

## Quick Reference: Implementation Checklist

### Files to Create

- [ ] `apps/signatures/custody_service.py` - Certificate generation service
- [ ] `templates/emails/signature_verified_with_certificate.html` - Signer email
- [ ] `templates/emails/new_signature_notification_creator.html` - Creator email
- [ ] `tests/test_custody_service.py` - Unit tests
- [ ] `tests/test_custody_integration.py` - Integration tests

### Files to Modify

- [ ] `apps/signatures/models.py` - Add custody chain fields
- [ ] `apps/signatures/tasks.py` - Integrate certificate generation
- [ ] `apps/signatures/admin.py` - Add custody certificate display
- [ ] `apps/signatures/urls.py` - Add download endpoints
- [ ] `apps/signatures/views.py` - Add download views
- [ ] `apps/petitions/urls.py` - Add bulk download endpoint
- [ ] `apps/petitions/views.py` - Add bulk download view
- [ ] `apps/core/tasks.py` - Add email notification tasks
- [ ] `templates/petitions/petition_detail.html` - Add bulk download button
- [ ] `requirements.txt` - Add requests library (if not present)

### Database Changes

- [ ] Add `custody_certificate_pdf` field
- [ ] Add `custody_certificate_url` field
- [ ] Add `verification_evidence` field
- [ ] Add `verification_hash` field
- [ ] Add `chain_of_custody` field
- [ ] Add `processing_started_at` field
- [ ] Add `processing_completed_at` field
- [ ] Add `certificate_generated_at` field

### Email Notifications

- [ ] Signer receives custody certificate after verification
- [ ] Creator receives notification when someone signs (with certificate)
- [ ] Both emails contain download links
- [ ] Test email templates in development
- [ ] Configure email retry logic

### Download Endpoints

- [ ] Individual certificate download: `/assinaturas/certificate/<uuid>/`
- [ ] Certificate verification API: `/assinaturas/verify-certificate/<uuid>/`
- [ ] Bulk download: `/peticoes/<uuid>/download-all-signatures/`
- [ ] Permission checks (only creator can bulk download)
- [ ] ZIP generation with all PDFs and certificates

### Testing Requirements

- [ ] Unit tests for custody service functions
- [ ] Integration tests for email delivery
- [ ] Test bulk download with 1, 10, 100+ signatures
- [ ] Test ZIP file structure and content
- [ ] Test manifest CSV accuracy
- [ ] Test verification hash calculation
- [ ] Test certificate PDF generation
- [ ] Test S3 upload/download

---

## Conclusion

This implementation guide provides a comprehensive roadmap for adding custody chain certification to the Petição Brasil platform with **three distribution scenarios**:

### What the System Will Do

- ✅ Generate professional custody certificates for all approved signatures
- ✅ Store immutable verification evidence with cryptographic hashing
- ✅ **Deliver certificates to signers** via email immediately after verification
- ✅ **Notify petition creators** when signatures are received (with certificate access)
- ✅ **Enable bulk download** for creators to get all signatures + certificates
- ✅ Provide public API for certificate verification
- ✅ Maintain complete audit trail for legal compliance
- ✅ Support forensic analysis with detailed verification evidence

### Distribution Summary

| Who | When | What They Get | How |
|-----|------|---------------|-----|
| **Signer** | After signature approved | Custody certificate + signed PDF | Email with download links |
| **Creator** | Each new signature | Custody certificate + signed PDF | Email notification |
| **Creator** | On-demand | ALL signatures + certificates | ZIP download (bulk) |

### Benefits

**For Signers:**
- Official proof of participation
- Legal evidence of signature verification
- Downloadable certificate anytime

**For Petition Creators:**
- Real-time notification of new signatures
- Immediate access to verification evidence
- Complete evidence package via bulk download
- Easy archival and legal submission

**For the Platform:**
- Enhanced trust and transparency
- Legal compliance and non-repudiation
- Complete forensic audit trail
- Professional evidence management

By following this guide step-by-step, you'll create a robust chain of custody system that enhances trust, transparency, and legal validity of digital signatures on the platform, while providing convenient access to all stakeholders.

---

**Document Status:** Ready for Implementation  
**Estimated Implementation Time:** 4-6 days  
**Priority:** High  
**Dependencies:** None (all required infrastructure exists)  
**New Dependencies:** `requests` library (for bulk download)

---

