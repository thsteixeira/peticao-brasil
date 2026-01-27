# LGPD Compliance Implementation Plan
**Petição Brasil - Lei Geral de Proteção de Dados**

**Document Version:** 1.0  
**Created:** January 24, 2026  
**Status:** Planning Phase  
**Priority:** Critical

---

## Executive Summary

This document outlines the implementation plan to achieve full LGPD (Lei Geral de Proteção de Dados - Law 13.709/2018) compliance for the Petição Brasil platform. While the platform has strong foundational security and privacy measures, several critical requirements for LGPD compliance are currently missing.

**Current Compliance Status:** ~75% (Core user rights mechanisms exist via email)  
**Target Compliance Status:** 100% (Legal requirements)  
**Estimated Implementation Time:** 4-6 weeks  
**Estimated Effort:** 47-68 hours (documentation and process implementation)  
**Organization Size:** Small organization (allows flexible DPO designation)

**Important Clarification:** The platform is currently LGPD-compliant for user rights fulfillment through email-based mechanisms. This plan focuses exclusively on:
1. **Critical gaps** (ROPA, DPO, DPAs, breach process) - legally required
2. **No automation implementation** - email-based mechanisms remain in place
3. **Single email contact** (contato@peticaobrasil.com.br) - handles all LGPD inquiries and DPO responsibilities

**Small Organization Advantage:** LGPD Art. 41 allows small organizations to designate existing staff (owner/admin) as DPO without requiring dedicated full-time personnel or specialized certification. This significantly reduces compliance costs while maintaining full legal compliance.

**Self-service automation** (data export, deletion, profile editing) is documented for future consideration but **not part of current scope**.

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Gap Analysis](#gap-analysis)
3. [Data Mapping (ROPA)](#data-mapping-ropa)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Phase 1: Critical Requirements](#phase-1-critical-requirements)
6. [Phase 2: Data Retention Automation](#phase-2-data-retention-automation-optional-enhancement)
7. [Technical Specifications](#technical-specifications)
9. [Testing & Validation](#testing--validation)
10. [Maintenance & Monitoring](#maintenance--monitoring)

---

## Current State Assessment

### ✅ Already Implemented

| Feature | Status | Location | LGPD Article |
|---------|--------|----------|--------------|
| Privacy Policy | ✅ Complete | `templates/static_pages/privacy.html` | Art. 9 |
| Terms of Use | ✅ Complete | `templates/static_pages/terms.html` | Art. 8 |
| Data Controller Identification | ✅ Complete | Privacy Policy | Art. 37 |
| Legal Bases Documentation | ✅ Complete | Privacy Policy | Art. 7 |
| CPF Hashing (SHA-256) | ✅ Complete | `apps/signatures/models.py` | Art. 46 |
| Password Encryption (bcrypt) | ✅ Complete | Django default | Art. 46 |
| IP Address Hashing | ✅ Complete | `apps/signatures/models.py` | Art. 46 |
| SSL/TLS Encryption | ✅ Complete | Middleware/Config | Art. 46 |
| Consent Checkboxes | ✅ Complete | Forms | Art. 8 |
| Content Security Policy | ✅ Complete | `apps/core/middleware.py` | Art. 46 |
| Audit Logging (ModerationLog) | ✅ Complete | `apps/core/models.py` | Art. 37 |
| Data Retention Policy (documented) | ⚠️ Documented only | `DOCS/legal_docs/security-and-sanitization.md` | Art. 15, 16 |

### ❌ Missing Critical Requirements

| Requirement | Priority | LGPD Article | Impact | Current Status |
|-------------|----------|--------------|---------|----------------|
| Data Mapping (ROPA) | 🔴 Critical | Art. 37 | Legal obligation | ❌ Missing |
| DPO Designation | 🔴 Critical | Art. 41 | Legal obligation | ❌ Missing |
| Breach Notification Process | 🔴 Critical | Art. 48 | Incident response | ❌ Missing |
| Data Processing Agreements | 🔴 Critical | Art. 46 | Third-party liability | ❌ Missing |
| **Mechanism for User Rights** | 🔴 Critical | Art. 18 | User rights | ✅ **Email-based (compliant)** |
| Self-Service Data Export | 🟡 High | Art. 18, II | Scalability improvement | ⚠️ Optional enhancement |
| Self-Service Account Deletion | 🟡 High | Art. 18, VI | Scalability improvement | ⚠️ Optional enhancement |
| Self-Service Profile Editing | 🟡 High | Art. 18, III | Scalability improvement | ⚠️ Optional enhancement |
| Automated Data Retention | 🟡 High | Art. 15, 16 | Efficiency | ⚠️ Optional enhancement |
| Consent Withdrawal Mechanism | 🟡 High | Art. 8, § 5º | User rights | ✅ **Email-based (compliant)** |
| Privacy Dashboard | 🟢 Medium | Art. 18 | User experience | ⚠️ Optional enhancement |
| Privacy Impact Assessment | 🟢 Medium | Art. 38 | Best practice | ⚠️ Optional enhancement |
| Consent Audit Trail | 🟢 Medium | Art. 37 | Accountability | ⚠️ Optional enhancement |

---

## Gap Analysis

### 1. Data Subject Rights (Direitos dos Titulares)

**Current State:** Privacy policy lists rights with email-based fulfillment mechanism (contato@peticaobrasil.com.br).  
**LGPD Compliance:** ✅ **Email-based fulfillment is legally compliant** - Art. 18 requires mechanisms for users to exercise rights but does not mandate self-service automation.  
**Gap:** Manual email process is slow and non-scalable for growing platform.  
**Recommended:** Automated self-service portal for operational efficiency and better user experience.

**Enhancement Opportunities (Not Legally Required):**
- 🔵 Self-service data export (JSON/CSV format)
- 🔵 Self-service account deletion with signature anonymization
- 🔵 Self-service profile editing (name, email)
- 🔵 View data processing history dashboard
- 🔵 Self-service consent withdrawal interface
- 🔵 Self-service data anonymization requests

**Note:** All the above can continue to be fulfilled via email (current compliant method), but automation improves scalability and reduces response time from days to seconds.

### 2. Data Inventory & Mapping (ROPA)

**Current State:** No formal data inventory exists.  
**Gap:** Cannot demonstrate compliance with Art. 37 (Record of Processing Activities).  
**Required:** Comprehensive data mapping document.

### 3. Data Retention Automation

**Current State:** Policy documented but not enforced programmatically.  
**Gap:** Manual cleanup required, risk of non-compliance.  
**Required:** Automated Celery tasks for data lifecycle management.

### 4. Organizational Requirements

**Current State:** No DPO designated, no breach response plan.  
**Gap:** Non-compliance with organizational requirements.  
**Required:** Formal DPO appointment and incident response procedures.

---

## Data Mapping (ROPA)

### Record of Processing Activities

As required by **LGPD Art. 37**, the following data inventory must be maintained:

#### 1. User Account Data

| Field | Type | Legal Basis | Purpose | Retention | Encryption |
|-------|------|-------------|---------|-----------|------------|
| `username` | Personal | Consent (Art. 7, I) | Platform authentication | While active + 5 years | No (non-sensitive) |
| `first_name` | Personal | Consent (Art. 7, I) | User identification | While active + 5 years | No (non-sensitive) |
| `last_name` | Personal | Consent (Art. 7, I) | User identification | While active + 5 years | No (non-sensitive) |
| `email` | Personal | Consent (Art. 7, I) | Communication, authentication | While active + 5 years | No (non-sensitive) |
| `password` | Sensitive | Consent (Art. 7, I) | Authentication | While active + 5 years | Yes (bcrypt) |
| `date_joined` | Non-personal | Legitimate interest | Audit trail | Indefinite | No |
| `is_active` | Non-personal | Legitimate interest | Access control | Indefinite | No |

**Data Controller:** Petição Brasil  
**Data Processors:** Heroku (hosting), AWS (backups)  
**International Transfer:** Yes (AWS US servers, DPA required)  
**Data Subjects:** Registered users (18+ years)

#### 2. Petition Data

| Field | Type | Legal Basis | Purpose | Retention | Encryption |
|-------|------|-------------|---------|-----------|------------|
| `title` | Non-personal | Legitimate interest (Art. 7, IX) | Public information | While active + 5 years | No |
| `description` | Non-personal | Legitimate interest (Art. 7, IX) | Public information | While active + 5 years | No |
| `creator` (FK) | Personal | Legitimate interest (Art. 7, IX) | Attribution | While active + 5 years | No |
| `signature_goal` | Non-personal | Legitimate interest | Platform functionality | While active + 5 years | No |

**Data Sharing:** Publicly accessible on platform  
**Cross-border Transfer:** Yes (CDN, DPA required)

#### 3. Signature Data (Most Sensitive)

| Field | Type | Legal Basis | Purpose | Retention | Encryption |
|-------|------|-------------|---------|-----------|------------|
| `full_name` | Personal | Legitimate interest (Art. 7, IX) | Democratic participation | 10 years | No |
| `cpf_hash` | Sensitive | Legal obligation (Art. 7, II) | Duplicate prevention, verification | 10 years | Yes (SHA-256) |
| `email` | Personal | Legitimate interest (Art. 7, IX) | Confirmation, updates | 10 years | No |
| `city` | Personal | Legitimate interest | Geographic statistics | 10 years | No |
| `state` | Personal | Legitimate interest | Geographic statistics | 10 years | No |
| `signed_pdf` | Sensitive | Legal obligation (Art. 7, II) | Legal evidence | 10 years | Yes (SSL, S3 encryption) |
| `certificate_info` | Sensitive | Legal obligation (Art. 7, II) | Digital signature validation | 10 years | No (structured JSON) |
| `ip_address_hash` | Personal | Legitimate interest | Fraud prevention, audit | 6 months | Yes (SHA-256) |
| `user_agent` | Personal | Legitimate interest | Fraud detection | 6 months | No |

**Legal Retention:** 10 years (Código Civil Art. 205 - prescription period)  
**Special Category:** Digital signatures have legal value, cannot be deleted before retention period  
**Anonymization:** Rejected signatures anonymized after 90 days

#### 4. Audit & Security Logs

| Field | Type | Legal Basis | Purpose | Retention | Encryption |
|-------|------|-------------|---------|-----------|------------|
| `moderator` (FK) | Personal | Legal obligation | Accountability | 5 years | No |
| `action_type` | Non-personal | Legal obligation | Audit trail | 5 years | No |
| `ip_address` | Personal | Legal obligation (Marco Civil) | Security, compliance | 6 months | No |
| `created_at` | Non-personal | Legal obligation | Temporal tracking | 5 years | No |

**Legal Requirement:** Marco Civil da Internet (Lei 12.965/2014) Art. 15  
**Retention:** 6 months minimum for access logs

#### 5. Third-Party Data Processors

| Processor | Service | Data Processed | Location | DPA Status |
|-----------|---------|----------------|----------|------------|
| Heroku (Salesforce) | Application hosting | All application data | USA | ❌ Required |
| AWS S3 | File storage (PDFs) | Signed PDFs, certificates | USA/Brazil | ❌ Required |
| Cloudflare | CDN, DDoS protection | Access logs, cached content | Global | ❌ Required |
| Gov.br | Digital signature | Certificate validation | Brazil | ✅ Government |

**Required Action:** Execute Data Processing Agreements (DPA) with all processors  
**LGPD Reference:** Art. 46 (International data transfers)

---

## Implementation Roadmap

### Overview Timeline

**Implementation Timeline (Critical Legal Requirements Only)**
```
Week 1-2:   ROPA Documentation + DPO Designation
Week 3-4:   Data Processing Agreements (DPAs) + Breach Notification Process
Week 5-6:   Testing, Documentation & Compliance Review
```

**Optional Future Enhancements (Not in Current Scope):**
- Self-service data export, deletion, and profile editing
- Automated data retention tasks
- Consent management dashboard
- Privacy dashboard interface
- Enhanced audit logging

**Current Focus:** Achieve 100% legal compliance using existing email-based mechanisms for user rights fulfillment.

### Resource Allocation (Small Organization)

| Role | Hours/Week | Total Hours |
|------|------------|-------------|
| Owner/Admin (Documentation) | 10-15 | 20-30 |
| Legal Consultant (External) | 5-10 | 14-22 |
| Owner/Admin (DPO Designation) | 1-2 | 3-4 |

**Note for Small Organizations:**
- No dedicated staff required
- Owner/admin acts as DPO and handles documentation
- External legal review only for DPAs and critical compliance questions
- No development work required - documentation and process-based only

---

## Phase 1: Critical Legal Requirements (IMPLEMENTATION SCOPE)
**Duration:** 4-6 weeks  
**Priority:** 🔴 Critical  
**Effort:** 40-60 hours (documentation & processes)

**Phase 1 Focus:** This phase addresses legally required documentation and processes ONLY:
- ✅ Data Mapping (ROPA) - Document all data processing activities
- ✅ DPO Designation - Appoint and publish Data Protection Officer
- ✅ Data Processing Agreements - Execute DPAs with third-party processors
- ✅ Breach Notification Process - Document incident response procedures

**Not Included:** Self-service automation features. The current email-based mechanism (contato@peticaobrasil.com.br) satisfies LGPD Art. 18 user rights requirements.

### 1.1 User Rights Fulfillment (Current Implementation)
**LGPD Article:** Art. 18  
**Status:** ✅ **COMPLIANT** via email (contato@peticaobrasil.com.br)  
**Implementation:** Email-based request handling

**Current Process:**
Users can exercise all LGPD rights by emailing contato@peticaobrasil.com.br:
- **Access (Art. 18, II):** Data export provided within 15 days
- **Correction (Art. 18, III):** Profile updates processed via email
- **Deletion (Art. 18, VI):** Account deletion with signature anonymization
- **Portability (Art. 18, V):** Data provided in JSON format
- **Consent Revocation (Art. 8, §5º):** Processed via email

**No Development Required:** This mechanism is legally compliant. 

**Action Required:** Update Privacy Policy and Terms of Use templates to explicitly inform users about their LGPD rights and the email-based process to exercise them.

**Template Updates:**

**File:** `templates/static_pages/privacy.html`

Add a new section detailing user rights:

```html
<h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Seus Direitos (LGPD)</h2>
<p>
    Conforme a Lei Geral de Proteção de Dados (LGPD), você tem os seguintes direitos 
    em relação aos seus dados pessoais:
</p>

<div class="bg-blue-50 border-l-4 border-blue-600 p-6 my-6">
    <h3 class="text-xl font-bold text-gray-900 mb-4">Como exercer seus direitos</h3>
    <p class="mb-4">
        Para exercer qualquer um dos direitos abaixo, envie um email para 
        <a href="mailto:contato@peticaobrasil.com.br" class="text-blue-600 hover:underline font-bold">
            contato@peticaobrasil.com.br
        </a> 
        identificando-se e especificando sua solicitação.
    </p>
    <p class="text-sm text-gray-700">
        <strong>Prazo de resposta:</strong> Até 15 dias corridos a partir do recebimento da solicitação.
    </p>
</div>

<div class="space-y-4">
    <div class="border-l-4 border-green-500 pl-4">
        <h4 class="font-bold text-gray-900">📋 Direito de Acesso (Art. 18, II)</h4>
        <p class="text-sm text-gray-700">
            Solicitar cópia de todos os dados pessoais que mantemos sobre você, 
            incluindo informações de conta, petições criadas e assinaturas.
        </p>
    </div>

    <div class="border-l-4 border-blue-500 pl-4">
        <h4 class="font-bold text-gray-900">✏️ Direito de Correção (Art. 18, III)</h4>
        <p class="text-sm text-gray-700">
            Solicitar a correção de dados incompletos, inexatos ou desatualizados.
        </p>
    </div>

    <div class="border-l-4 border-purple-500 pl-4">
        <h4 class="font-bold text-gray-900">🗑️ Direito de Exclusão (Art. 18, VI)</h4>
        <p class="text-sm text-gray-700">
            Solicitar a eliminação de seus dados pessoais. 
            <strong>Importante:</strong> Assinaturas digitais devem ser mantidas por 10 anos 
            conforme legislação, mas seus dados pessoais serão anonimizados.
        </p>
    </div>

    <div class="border-l-4 border-orange-500 pl-4">
        <h4 class="font-bold text-gray-900">📤 Direito de Portabilidade (Art. 18, V)</h4>
        <p class="text-sm text-gray-700">
            Solicitar seus dados pessoais em formato estruturado (JSON) para transferência 
            a outro serviço.
        </p>
    </div>

    <div class="border-l-4 border-red-500 pl-4">
        <h4 class="font-bold text-gray-900">🚫 Direito de Revogação de Consentimento (Art. 8, §5º)</h4>
        <p class="text-sm text-gray-700">
            Revogar seu consentimento para processamento de dados em qualquer momento, 
            quando o tratamento for baseado em consentimento.
        </p>
    </div>

    <div class="border-l-4 border-yellow-500 pl-4">
        <h4 class="font-bold text-gray-900">ℹ️ Direito de Informação (Art. 18, I)</h4>
        <p class="text-sm text-gray-700">
            Solicitar informações sobre quais dados pessoais tratamos, finalidade, 
            compartilhamento com terceiros e período de retenção.
        </p>
    </div>

    <div class="border-l-4 border-gray-500 pl-4">
        <h4 class="font-bold text-gray-900">⚖️ Direito de Oposição (Art. 18, §2º)</h4>
        <p class="text-sm text-gray-700">
            Opor-se ao tratamento de seus dados quando realizado com base em 
            legítimo interesse.
        </p>
    </div>
</div>

<div class="bg-yellow-50 border-l-4 border-yellow-400 p-6 my-6">
    <p class="text-sm text-gray-800">
        <strong>Nota sobre retenção legal:</strong> Alguns dados (como assinaturas digitais) 
        possuem período de retenção legal obrigatório de 10 anos conforme o Código Civil Brasileiro 
        (Art. 205). Nesses casos, os dados podem ser anonimizados mas não completamente excluídos.
    </p>
</div>
```

**File:** `templates/static_pages/terms.html`

Add a reference to LGPD rights in Section 7:

```html
<h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">7. Privacidade e Proteção de Dados</h2>
<p>
    A coleta e tratamento de dados pessoais segue nossa 
    <a href="{% url 'petitions:privacy_policy' %}" class="text-blue-600 hover:underline">Política de Privacidade</a>, 
    em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018).
</p>

<div class="bg-blue-50 border-l-4 border-blue-600 p-6 my-4">
    <h3 class="text-lg font-bold text-gray-900 mb-2">Exercício de Direitos LGPD</h3>
    <p class="mb-2">
        Você pode exercer seus direitos de acesso, correção, exclusão, portabilidade 
        e outros previstos na LGPD enviando email para:
    </p>
    <p class="font-bold">
        <a href="mailto:contato@peticaobrasil.com.br" class="text-blue-600 hover:underline">
            contato@peticaobrasil.com.br
        </a>
    </p>
    <p class="text-sm text-gray-700 mt-2">
        Consulte nossa 
        <a href="{% url 'petitions:privacy_policy' %}" class="text-blue-600 hover:underline">
            Política de Privacidade
        </a> 
        para informações detalhadas sobre seus direitos e como exercê-los.
    </p>
</div>
```

**Effort:** 2-3 hours  
**Success Criteria:**
- ✅ Privacy policy explicitly lists all LGPD rights
- ✅ Clear instructions for exercising rights via email
- ✅ Response time commitment stated (15 days)
- ✅ Legal retention periods explained
- ✅ Terms of Use references LGPD rights mechanism

---

### 1.2 Data Mapping Documentation (ROPA)
**LGPD Article:** Art. 37  
**Effort:** 16-20 hours

**Deliverable:** Complete ROPA (Record of Processing Activities) document

**File:** `DOCS/legal_docs/data-mapping-ropa.md`

Include all tables from section above, plus:
- Data flow diagrams
- Third-party processor list with DPA status
- Data retention schedules
- Access control matrix
- Incident response contacts

**Success Criteria:**
- ✅ All personal data fields documented
- ✅ Legal bases identified for each field
- ✅ Retention periods specified
- ✅ Third-party processors listed
- ✅ International transfers documented

---

### 1.3 DPO Designation (Small Organization Approach)
**LGPD Article:** Art. 41  
**Effort:** 2-3 hours

**Note for Small Organizations:** LGPD allows small organizations to designate an existing team member (owner, admin, or manager) as DPO without requiring a dedicated full-time role or specialized certification.

**Actions:**
1. Formally designate owner/admin as DPO (Encarregado de Dados)
2. Update privacy policy with DPO contact information
3. Use existing email: **contato@peticaobrasil.com.br** (consolidated contact)
4. Document DPO responsibilities internally
5. Publish designation on website

**Rationale for Single Email:**
- ✅ LGPD-compliant for small organizations
- ✅ Simplifies user experience (one contact for all inquiries)
- ✅ Reduces administrative overhead
- ✅ Same response SLA applies (15 days)

**Template Update:** `templates/static_pages/privacy.html`

```html
<h2>Encarregado de Proteção de Dados (DPO)</h2>
<p>
    Conforme Art. 41 da LGPD, designamos um Encarregado de Proteção de Dados para 
    atuar como canal de comunicação entre titulares de dados, controlador e ANPD:
</p>
<div class="bg-blue-50 p-4 rounded-lg my-4">
    <p class="mb-2"><strong>Responsável:</strong> [Nome do Proprietário/Administrador]</p>
    <p class="mb-4">
        <strong>Email:</strong> 
        <a href="mailto:contato@peticaobrasil.com.br" class="text-blue-600 hover:underline font-bold">
            contato@peticaobrasil.com.br
        </a>
    </p>
    <p class="text-sm text-gray-700 mb-2"><strong>Responsabilidades do DPO:</strong></p>
    <ul class="text-sm text-gray-700 space-y-1">
        <li>✓ Receber e responder solicitações de titulares de dados</li>
        <li>✓ Prestar esclarecimentos sobre práticas de proteção de dados</li>
        <li>✓ Atuar como canal de comunicação com a ANPD</li>
        <li>✓ Orientar sobre conformidade com a LGPD</li>
    </ul>
    <p class="text-sm text-gray-600 mt-3">
        <em>Prazo de resposta: até 15 dias corridos</em>
    </p>
</div>
```

**Success Criteria:**
- ✅ Owner/admin formally designated as DPO
- ✅ Contact information published on privacy policy
- ✅ Email (contato@) monitored daily for all inquiries
- ✅ Response SLA: 15 days maximum
- ✅ DPO responsibilities documented internally

---

### 1.4 Breach Notification Process (Documentation Only)
**LGPD Article:** Art. 48  
**Effort:** 4-6 hours

**Deliverable:** Incident Response Plan document

**File:** `DOCS/legal_docs/incident-response-plan.md`

**Note:** This is documentation only - no development required. Focus on preparing procedures and templates for potential data breach incidents.

**Document Contents:**

1. **Incident Classification Levels**
   - Low Risk: Minimal personal data exposure, no sensitive data
   - Medium Risk: Limited personal data exposure, potential impact
   - High Risk: Sensitive data exposure (CPF, passwords, signed PDFs)
   - Critical: Mass data breach, significant harm to users

2. **Response Team & Roles**
   - **Incident Commander:** Owner/Admin (DPO)
   - **Technical Lead:** System administrator
   - **Communications Lead:** Owner/Admin (DPO)
   - **Legal Contact:** External legal consultant

3. **Response Timeline**
   - **Hour 0:** Incident detected and classified
   - **Hour 1:** Response team activated, initial assessment
   - **Hour 4:** Containment measures implemented
   - **Hour 24:** Impact assessment completed
   - **Hour 72:** ANPD notification (if required)
   - **Week 1:** Affected users notified

4. **ANPD Notification Template**
   - Incident description and classification
   - Data categories affected
   - Number of affected users
   - Potential consequences
   - Security measures in place
   - Mitigation actions taken
   - Contact information (DPO)

5. **User Notification Template (Email)**
   - Clear explanation of what happened
   - What data was affected
   - What actions platform is taking
   - What users should do (if any)
   - Contact for questions (contato@peticaobrasil.com.br)
   - Apology and commitment to security

6. **Post-Incident Review**
   - Root cause analysis
   - Timeline reconstruction
   - Lessons learned
   - Security improvements needed
   - Documentation updates

**Success Criteria:**
- ✅ Incident classification system documented
- ✅ Response team roles clearly defined
- ✅ ANPD notification template ready
- ✅ User notification email template prepared
- ✅ 72-hour notification timeline understood
- ✅ Post-incident review process established

**Note on Consent Management:** Email-based consent withdrawal (via contato@) is sufficient for current compliance. Self-service consent tracking (UserConsent model) is documented in Phase 3 as an optional enhancement.

---

### 1.5 Third-Party Data Processing Agreements (Verification & Documentation)
**LGPD Article:** Art. 46  
**Effort:** 4-6 hours (verification and documentation)

**Important Note:** Most major cloud providers (AWS, Heroku/Salesforce, Cloudflare) have **standard DPAs that are automatically included** in their terms of service. You don't need to negotiate custom agreements - you just need to verify and document them.

**Actions:**

1. **AWS:**
   - ✅ Standard AWS Data Processing Addendum (DPA) automatically applies
   - Review: https://aws.amazon.com/compliance/gdpr-center/
   - Covers GDPR (which LGPD mirrors closely)
   - **Action:** Download and save copy for records

2. **Heroku/Salesforce:**
   - ✅ Salesforce Data Processing Addendum available
   - Review: https://www.salesforce.com/company/legal/data-processing-addendum/
   - **Action:** Accept DPA in account settings if not already done

3. **Cloudflare:**
   - ✅ Standard Data Processing Addendum available
   - Review: https://www.cloudflare.com/cloudflare-customer-dpa/
   - **Action:** Review and save copy

4. **Documentation:**
   - Create a folder: `DOCS/legal_docs/processor-agreements/`
   - Save PDF copies of all DPAs
   - Document in ROPA which processors have active DPAs
   - Note acceptance dates and review schedule

**DPA Requirements Already Covered by Standard Agreements:**
- ✅ Data categories processed
- ✅ Security measures
- ✅ Breach notification obligations
- ✅ Sub-processor restrictions
- ✅ Data subject rights support
- ✅ Audit rights
- ✅ International transfer safeguards (Standard Contractual Clauses)

**Success Criteria:**
- ✅ Verified that DPAs are active for all three processors
- ✅ PDF copies saved in legal documentation folder
- ✅ DPA status documented in ROPA
- ✅ Annual review scheduled (check for DPA updates)

---

## Phase 2: Data Retention Automation (Optional Enhancement)
**Duration:** 1-2 weeks  
**Priority:** 🟡 High  
**Effort:** 12-16 hours (development)

**Important Note:** Phase 2 is optional but highly recommended. While not legally required for LGPD compliance (manual data cleanup is acceptable), automation reduces operational overhead and ensures consistent enforcement of retention policies.

### 2.1 Automated Data Retention Tasks
**LGPD Article:** Art. 15, 16 (Data retention minimization)  
**Effort:** 12-16 hours

**Implementation:** Celery periodic tasks for automated data lifecycle management

**File:** `apps/core/tasks.py`

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.signatures.models import Signature
from apps.core.models import ModerationLog
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_rejected_signatures():
    """
    Anonymize rejected signatures after 90 days.
    LGPD Art. 16 - Data retention policy.
    """
    cutoff_date = timezone.now() - timedelta(days=90)
    
    rejected_signatures = Signature.objects.filter(
        verification_status='rejected',
        created_at__lt=cutoff_date,
        full_name__isnull=False  # Not already anonymized
    )
    
    count = 0
    for signature in rejected_signatures:
        signature.full_name = "[Rejeitada - Anonimizada]"
        signature.email = f"anonimizado_{signature.uuid}@lgpd.local"
        signature.cpf_hash = None
        signature.signed_pdf = None
        signature.certificate_info = None
        signature.ip_address_hash = None
        signature.user_agent = None
        signature.save()
        count += 1
    
    logger.info(f"Anonymized {count} rejected signatures older than 90 days")
    return count


@shared_task
def cleanup_access_logs():
    """
    Delete IP address logs after 6 months.
    Marco Civil da Internet - Art. 15 (minimum 6 months retention).
    """
    cutoff_date = timezone.now() - timedelta(days=180)
    
    # Clear IP from old moderation logs
    old_logs = ModerationLog.objects.filter(
        created_at__lt=cutoff_date,
        ip_address__isnull=False
    )
    
    count = old_logs.update(ip_address=None)
    logger.info(f"Cleared IP addresses from {count} old moderation logs")
    
    # Clear IP hash from old signatures (keep other data)
    old_signatures = Signature.objects.filter(
        created_at__lt=cutoff_date,
        ip_address_hash__isnull=False
    )
    
    count2 = old_signatures.update(ip_address_hash=None, user_agent=None)
    logger.info(f"Cleared IP/user agent from {count2} old signatures")
    
    return count + count2


@shared_task
def cleanup_inactive_accounts():
    """
    Anonymize accounts inactive for 5+ years with no petitions.
    LGPD Art. 15 - Retention period limitation.
    """
    from django.contrib.auth.models import User
    
    cutoff_date = timezone.now() - timedelta(days=1825)  # 5 years
    
    inactive_users = User.objects.filter(
        last_login__lt=cutoff_date,
        petitions_created__isnull=True,  # No petitions
        is_staff=False,
        is_active=True
    )
    
    count = 0
    for user in inactive_users:
        # Check if user has any signatures
        from apps.signatures.models import Signature
        has_signatures = Signature.objects.filter(email=user.email).exists()
        
        if not has_signatures:
            # Safe to delete completely
            user.delete()
            count += 1
        else:
            # Anonymize but keep for signature linkage
            user.username = f"usuario_inativo_{user.id}"
            user.email = f"inativo_{user.id}@anonimo.local"
            user.first_name = "[Inativo]"
            user.last_name = ""
            user.is_active = False
            user.save()
            count += 1
    
    logger.info(f"Processed {count} inactive accounts (5+ years)")
    return count
```

**Celery Configuration:** `config/settings/base.py`

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-rejected-signatures': {
        'task': 'apps.core.tasks.cleanup_rejected_signatures',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly, Sunday 2 AM
    },
    'cleanup-access-logs': {
        'task': 'apps.core.tasks.cleanup_access_logs',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # Monthly, 1st day 3 AM
    },
    'cleanup-inactive-accounts': {
        'task': 'apps.core.tasks.cleanup_inactive_accounts',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),  # Monthly, 1st day 4 AM
    },
}
```

**Success Criteria:**
- ✅ Rejected signatures auto-anonymized after 90 days
- ✅ IP addresses cleared after 6 months
- ✅ Inactive accounts processed after 5 years
- ✅ Tasks run automatically via Celery Beat
- ✅ Execution logged for audit

---

## Technical Specifications

### Database Changes (Phase 1 - Critical Requirements)

**No new models required for Phase 1 compliance.**

**Existing Models Sufficient:**
- `User` (Django) - Tracks `date_joined` for terms acceptance
- `ModerationLog` - Provides audit trail
- `Signature` - Contains data requiring retention enforcement

**Model Modifications:**
- None required for Phase 1 or Phase 2

**Migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

### Celery Tasks

**New periodic tasks:**
- `cleanup_rejected_signatures` - Weekly
- `cleanup_access_logs` - Monthly
- `cleanup_inactive_accounts` - Monthly

**Configuration:**
```python
# config/celery.py
app.conf.beat_schedule = {
    'lgpd-data-retention-weekly': {
        'task': 'apps.core.tasks.cleanup_rejected_signatures',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
    'lgpd-data-retention-monthly': {
        'task': 'apps.core.tasks.cleanup_access_logs',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),
    },
}
```

### Security Considerations

1. **Password Confirmation:** All destructive actions require password re-entry
2. **Rate Limiting:** Data export limited to 1/hour per user
3. **Audit Logging:** All privacy actions logged with IP hash
4. **Encryption:** Exported data transmitted over HTTPS only
5. **Access Control:** Privacy functions require authentication

### Performance Impact

| Feature | Impact | Mitigation |
|---------|--------|------------|
| Data Export | Medium (DB queries) | Cache user data, limit frequency |
| Audit Logging | Low (async writes) | Use database indexes |
| Auto-Retention | Low (background tasks) | Run during off-peak hours |
| Consent Management | Minimal | Indexed queries |

---

## Testing & Validation

### Unit Tests

**File:** `tests/test_lgpd_compliance.py`

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.signatures.models import Signature
from apps.accounts.models import UserConsent
import json


class LGPDComplianceTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!@#'
        )
    
    def test_data_export_authenticated(self):
        """Test user can export their data when authenticated."""
        self.client.login(username='testuser', password='TestPass123!@#')
        response = self.client.get('/accounts/privacy/export-data/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        
        data = json.loads(response.content)
        self.assertIn('personal_information', data)
        self.assertEqual(data['personal_information']['email'], 'test@example.com')
    
    def test_data_export_requires_auth(self):
        """Test data export requires authentication."""
        response = self.client.get('/accounts/privacy/export-data/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_account_deletion_anonymizes_signatures(self):
        """Test account deletion anonymizes signatures per LGPD."""
        # Create petition and signature
        # ... setup code ...
        
        self.client.login(username='testuser', password='TestPass123!@#')
        response = self.client.post('/accounts/privacy/delete-account/', {
            'password_confirmation': 'TestPass123!@#'
        })
        
        # Verify user deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())
        
        # Verify signature anonymized
        signature = Signature.objects.first()
        self.assertEqual(signature.full_name, '[Usuário Removido]')
        self.assertIn('anonimo.local', signature.email)
    
    def test_consent_withdrawal(self):
        """Test user can withdraw consent."""
        self.client.login(username='testuser', password='TestPass123!@#')
        
        # Grant consent
        consent = UserConsent.objects.create(
            user=self.user,
            consent_type='email_updates',
            granted=True
        )
        
        # Withdraw consent
        response = self.client.post('/accounts/privacy/preferences/', {
            'email_updates': ''  # Unchecked
        })
        
        consent.refresh_from_db()
        self.assertFalse(consent.granted)
        self.assertIsNotNone(consent.revoked_at)
    
    def test_profile_edit_email_uniqueness(self):
        """Test email uniqueness validation in profile edit."""
        User.objects.create_user(
            username='other',
            email='taken@example.com',
            password='pass'
        )
        
        self.client.login(username='testuser', password='TestPass123!@#')
        response = self.client.post('/accounts/profile/edit/', {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'taken@example.com'
        })
        
        # Should fail
        self.assertFormError(response, 'form', 'email', 'Este email já está em uso.')
```

### Integration Tests

**Scenarios:**
1. Complete user journey: signup → create petition → delete account
2. Data export includes all related entities
3. Retention tasks run without errors
4. Consent changes reflect in email sending

### Manual Testing Checklist

- [ ] Data export downloads valid JSON file
- [ ] Account deletion shows confirmation page
- [ ] Active petitions prevent account deletion
- [ ] Profile edit saves changes correctly
- [ ] Privacy dashboard displays accurate statistics
- [ ] Consent preferences save correctly
- [ ] DPO contact information is visible
- [ ] Retention tasks execute on schedule

---

## Maintenance & Monitoring

### Ongoing Responsibilities

| Task | Frequency | Owner | Hours/Month |
|------|-----------|-------|-------------|
| Monitor contato@ inbox (LGPD requests) | Daily | Owner/Admin (DPO) | 5-10 |
| Review data access logs | Weekly | Owner/Admin | 2-4 |
| Update data mapping | Quarterly | Owner/Admin | 4 |
| Privacy policy review | Semi-annually | Legal Consultant | 4-8 |
| Compliance audit (optional) | Annually | External Auditor | 20-40 |
| Retention task monitoring | Monthly | Owner/Admin | 1-2 |
| User rights request processing | As needed | Owner/Admin (DPO) | Variable |

**Note:** Single email (contato@peticaobrasil.com.br) handles all user rights, DPO, and general platform inquiries.

### Metrics & KPIs

**Track monthly:**
- Number of data export requests
- Account deletion requests
- Consent withdrawal rate
- Data retention task execution success
- Average response time to rights requests
- Data breach incidents (target: 0)

### Alerts & Notifications

**Configure monitoring for:**
- Failed retention tasks
- Unusually high deletion requests (potential data breach)
- DPO email response SLA breach (>15 days)
- Unauthorized data access attempts
- Data export failures

### Documentation Updates

**Keep current:**
- Data mapping document (`DOCS/legal_docs/data-mapping-ropa.md`) - quarterly
- Privacy policy (`templates/static_pages/privacy.html`) - when processing changes
- DPA list (within ROPA document) - when adding processors
- Incident response plan (`DOCS/legal_docs/incident-response-plan.md`) - annually
- Training materials (`DOCS/legal_docs/`) - semi-annually

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Complete ROPA document exists
- ✅ DPO is designated and contact published
- ✅ Breach notification process is documented
- ✅ DPAs verified and documented
- ✅ Privacy policy and terms updated with LGPD rights

### Phase 2 Complete When:
- ✅ Automated retention tasks run successfully
- ✅ Tasks run automatically via Celery Beat
- ✅ Execution logged for audit

### Full LGPD Legal Compliance Achieved When:
- ✅ All personal data is mapped and documented (ROPA)
- ✅ DPO is designated and contact published
- ✅ All third-party processors have DPAs verified
- ✅ Breach notification process is documented
- ✅ User rights mechanism exists (email-based)
- ✅ Privacy policy is current and accessible
- ✅ Consent mechanisms are in place (email-based withdrawal)

### Operational Excellence Achieved When (Phase 2 - Optional):
- ✅ Automated retention policies are enforced
- ✅ Data cleanup happens automatically without manual intervention
- ✅ Compliance monitoring is automated

---

## Risk Assessment

### High Risk
- **Data Breach:** Unauthorized access to personal data
  - **Mitigation:** Enhanced logging, security monitoring, encryption
  - **Response:** Breach notification plan (Phase 2.3)

- **Non-compliance Penalties:** ANPD fines up to 2% revenue or R$ 50 million
  - **Mitigation:** Priority implementation of critical features
  - **Timeline:** Complete Phase 1 within 4 weeks

### Medium Risk
- **User Complaints:** ANPD complaints about data rights
  - **Mitigation:** Self-service portal, clear documentation
  - **Response:** 15-day SLA for all requests

- **Data Retention Failure:** Keeping data longer than allowed
  - **Mitigation:** Automated tasks, monitoring alerts
  - **Recovery:** Manual cleanup procedures documented

### Low Risk
- **Third-Party Breach:** Processor security incident
  - **Mitigation:** DPAs with breach notification clauses
  - **Response:** Activate incident response plan

---

## Budget & Resources

### Implementation Hours Breakdown

| Phase | Documentation | Legal Review | Process Setup | Total |
|-------|--------------|--------------|---------------|-------|
| ROPA Documentation | 16-20 | 4-6 | - | 20-26 |
| DPO Designation (Internal) | 2-3 | - | 1 | 3-4 |
| DPA Execution | 4-6 | 8-12 | 4-6 | 16-24 |
| Breach Process | 4-6 | 2-4 | 2-4 | 8-14 |
| **Total** | **26-35** | **14-22** | **7-11** | **47-68** |

**Note:** No development/coding required. All work is documentation and legal process implementation.

### External Costs (Estimates for Small Organizations)

**Essential:**
- Legal review (DPAs): R$ 3.000 - R$ 8.000 (one-time)
- LGPD consultation (optional): R$ 1.000 - R$ 3.000 (one-time guidance)

**Optional (Recommended for Growth):**
- Annual compliance audit: R$ 8.000 - R$ 15.000 (scaled for small platforms)
- External DPO consultant: R$ 500 - R$ 2.000/month (part-time, if needed)
- Compliance software: R$ 200 - R$ 800/month (optional)

### Total Estimated Cost (Small Organization)

**Minimum Viable Compliance:**
- **Internal Documentation:** 47-68 hours × internal hourly rate (owner/admin time)
- **Legal Review/DPAs:** R$ 3.000 - R$ 8.000 (one-time)
- **Optional LGPD Consultation:** R$ 1.000 - R$ 3.000 (one-time)
- **Total First Year (Minimum):** R$ 4.000 - R$ 11.000

**With Optional Enhancements:**
- **Annual Compliance Audit:** R$ 8.000 - R$ 15.000/year
- **External DPO Support:** R$ 6.000 - R$ 24.000/year (R$ 500-2.000/month)
- **Total First Year (Enhanced):** R$ 18.000 - R$ 50.000
- **Ongoing (annual):** R$ 14.000 - R$ 39.000/year

**Small Organization Advantage:** By designating internal staff as DPO and using a single contact email, the platform eliminates R$ 36.000-96.000/year in dedicated DPO salary costs while remaining fully LGPD-compliant.

---

## Conclusion

This implementation plan provides a comprehensive roadmap to achieve full LGPD compliance for the Petição Brasil platform. By following the phased approach over 12 weeks, the platform will:

1. **Meet all legal obligations** under LGPD
2. **Empower users** with self-service data rights
3. **Reduce compliance risk** through automation
4. **Build user trust** with transparent practices
5. **Establish accountability** through comprehensive documentation

**Next Steps:**
1. Review and approve this plan with stakeholders
2. Allocate development resources
3. Begin Phase 1 implementation immediately
4. Schedule legal review for DPAs
5. Designate DPO

**Timeline to Full Compliance:** 12 weeks from approval

---

## Appendices

### Appendix A: LGPD Articles Reference

- **Art. 7** - Legal bases for processing
- **Art. 8** - Consent requirements
- **Art. 9** - Transparency obligations
- **Art. 15, 16** - Data retention
- **Art. 18** - Data subject rights
- **Art. 37** - Record of processing activities
- **Art. 41** - Data Protection Officer
- **Art. 46** - International data transfers
- **Art. 48** - Breach notification

### Appendix B: Useful Resources

- **ANPD Website:** https://www.gov.br/anpd/
- **LGPD Full Text:** http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- **GDPR Comparison:** Many LGPD concepts mirror GDPR
- **ICP-Brasil Standards:** https://www.gov.br/iti/pt-br/assuntos/icp-brasil

### Appendix C: Templates

- Data Export JSON schema
- Account Deletion confirmation email
- Consent withdrawal confirmation
- Breach notification (user)
- Breach notification (ANPD)
- DPA template

---

## Document Organization

**This Plan Location:** `DOCS/plans/lgpd-compliance-implementation-plan.md`

**Related Legal Documents:**
- `DOCS/legal_docs/data-mapping-ropa.md` - Record of Processing Activities (to be created)
- `DOCS/legal_docs/incident-response-plan.md` - Breach notification procedures (to be created)
- `DOCS/legal_docs/privacy-impact-assessment.md` - PIA template (to be created)
- `DOCS/legal_docs/security-and-sanitization.md` - Security documentation (existing)

**Public-Facing Documents:**
- `templates/static_pages/privacy.html` - Privacy Policy (requires updates)
- `templates/static_pages/terms.html` - Terms of Use (requires updates)

---

**Document Status:** Ready for Review  
**Prepared By:** Development Team  
**Review Required:** Legal, Management, DPO  
**Approval Required:** CEO, CTO  
**Implementation Start:** Upon approval
