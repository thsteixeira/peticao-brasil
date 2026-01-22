# Democracia Direta - Overview

**Project Phase:** Planning  
**Document Version:** 1.0  
**Last Updated:** November 23, 2025  
**Status:** Draft

---

## Executive Summary

The **Democracia Direta** app is a platform that empowers citizens to create, sign, and manage public petitions for specific political causes.

### Core Value Proposition

- **For Citizens:** Create and sign legally valid petitions using official Brazilian government digital signatures
- **For Democracy:** Provide a transparent, secure platform for collective political expression
- **For the Platform:** Feature a comprehensive civic engagement tool

---

## Feature Objectives

### Primary Goals

1. **Enable Petition Creation**
   - Allow authenticated users to draft petitions on political causes
   - Support rich text formatting and cause categorization
   - Set petition goals (signature targets, deadlines)

2. **Implement Gov.br Digital Signature Integration**
   - Leverage Brazil's official electronic signature system
   - Ensure legal validity of signatures
   - Provide clear, step-by-step signing instructions

3. **Automate Signature Verification**
   - Validate uploaded signed PDFs against originals
   - Detect tampering or fraud attempts
   - Maintain audit trail for all signatures

4. **Ensure Security and Trust**
   - Sanitize all file uploads
   - Prevent duplicate signatures
   - Comply with LGPD (Brazilian data protection law)
   - Maintain public transparency of petition counts

### Secondary Goals

- SEO optimization for petition discovery
- Social media sharing capabilities
- Analytics dashboard for petition creators
- Email notifications for petition milestones
- Export capabilities for final petition documents

---

## User Personas

### 1. **Petition Creator (Activist)**
- **Profile:** Engaged citizen, NGO member, or community leader
- **Goals:** Create impactful petitions, reach signature goals, deliver to authorities
- **Pain Points:** Complex legal processes, lack of technical expertise
- **Needs:** Easy petition creation, clear guidance, credible signature collection

### 2. **Petition Signer (Citizen)**
- **Profile:** Brazilian citizen with CPF, varying digital literacy
- **Goals:** Support causes they believe in, ensure signature validity
- **Pain Points:** Complicated signing processes, security concerns
- **Needs:** Clear instructions, mobile-friendly experience, trust in platform

### 3. **Platform Administrator**
- **Profile:** Democracia Direta team member
- **Goals:** Moderate content, ensure platform integrity, support users
- **Needs:** Moderation tools, fraud detection, reporting capabilities

---

## Use Cases

### Primary Use Cases

#### UC1: Create a Petition (Authenticated Users Only)
1. User logs in/registers on Democracia Direta (required)
2. Navigates to "Create Petition" page
3. Fills petition form (title, description, category, goal)
4. Submits petition for publication
5. System generates unique PDF document
6. Petition goes live on platform

#### UC2: Sign a Petition (No Authentication Required)
1. **Anyone** discovers petition (browse/search/link) - no login needed
2. Reads petition content
3. Clicks "Sign This Petition"
4. Downloads auto-generated PDF
5. Follows tutorial to sign via Gov.br system
6. Returns to platform and uploads signed PDF
7. Fills verification form (name, CPF, email for confirmation)
8. System verifies signature automatically
9. Signature count increments publicly

#### UC3: Download Petition Bundle
1. Petition reaches goal or deadline
2. Creator downloads complete petition package
3. Package includes:
   - Original petition
   - All verified signatures
   - Signature list (anonymized/full based on settings)
   - Verification certificates

### Secondary Use Cases

- UC4: Share petition on social media
- UC5: Track petition progress
- UC6: Report inappropriate petition
- UC7: Export signature analytics
- UC8: Resend notification to complete signature

---

## High-Level Technical Approach

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│           Democracia Direta Platform                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │         Django Application                  │   │
│  │                                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │
│  │  │Petitions │  │Signatures│  │   Users  │  │   │
│  │  │          │  │          │  │          │  │   │
│  │  │  Models  │  │  Models  │  │  Auth    │  │   │
│  │  │  Views   │  │  Views   │  │  System  │  │   │
│  │  │  APIs    │  │  APIs    │  │          │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                        │                           │
│                        ▼                           │
│             ┌──────────────────────┐               │
│             │  PostgreSQL Database │               │
│             └──────────────────────┘               │
│                        │                           │
│                        ▼                           │
│             ┌──────────────────────┐               │
│             │  File Storage (S3)   │               │
│             │  - Petition PDFs     │               │
│             │  - Signed PDFs       │               │
│             └──────────────────────┘               │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Gov.br Sign System  │
              │   (External)          │
              └───────────────────────┘
```

### Technology Stack

- **Backend:** Django 4.x
- **Database:** PostgreSQL
- **PDF Generation:** ReportLab
- **PDF Processing:** PyPDF2 / pdfplumber / pyHanko
- **File Storage:** AWS S3
- **Signature Verification:** SHA-256 hashing + PDF signature validation
- **Frontend:** HTML/CSS/JS (Bootstrap 5 or Tailwind CSS)
- **Security:** Django file upload validators, ClamAV (optional)
- **Task Queue:** Celery + Redis
- **Email:** SendGrid or similar

### Key Components

1. **User Authentication:** Django's built-in authentication system with custom user profiles
2. **Template System:** Custom base templates with responsive design
3. **CAPTCHA Protection:** Cloudflare Turnstile for petition creation and signature submission
4. **Static Files:** Separate static file management with CDN support
5. **Background Tasks:** Celery for async PDF generation and verification
6. **Email System:** Transactional emails for notifications and confirmations

---

## Signature Verification Strategy

### Approach: Content Extraction + Unique Identifier + Digital Signature Validation

**The Challenge:**
When Gov.br adds a digital signature to a PDF, it modifies the file structure, changing the file hash. We cannot use simple file hash comparison.

**Solution: Multi-Layer Verification**

1. **PDF Generation Phase:**
   - Generate petition PDF with standardized structure
   - Embed unique petition identifier (UUID) in PDF metadata AND visible text
   - Extract and hash the **text content only** (not the file)
   - Store in database:
     - Petition UUID
     - Content hash (SHA-256 of normalized text)
     - Original PDF structure/template version
     - Original extracted text (for direct comparison)

2. **Signing Phase:**
   - User downloads PDF with embedded UUID
   - Goes to Gov.br system and signs the PDF
   - Gov.br adds digital signature layer (file changes, but content remains)
   - User uploads signed PDF back to our system

3. **Verification Phase (Multi-Step):**
   
   **Step 1: Extract & Compare Document Text**
   - Extract full text content from the **original petition PDF**
   - Extract full text content from the **uploaded signed PDF**
   - Normalize both texts (remove formatting, whitespace variations)
   - **Directly compare the two text strings** → Must be identical
   - Additionally calculate hash of signed PDF text
   - Compare with stored content hash → Must match
   - **This ensures the document text was not altered between generation and signing**
   
   **Step 2: Verify Petition UUID**
   - Extract UUID from PDF metadata and/or text
   - Match against database petition UUID → Must match
   
   **Step 3: Validate Digital Signature**
   - Check if PDF has valid digital signature
   - Verify signature is from Gov.br certificate authority
   - Extract signer's CPF from signature certificate
   
   **Step 4: Cross-Validate Form Data**
   - Compare CPF from signature with CPF from verification form
   - Compare name from signature with name from form
   - Check CPF hasn't already signed this petition (duplicate prevention)
   
   **Step 5: Fraud Detection**
   - Check if PDF was modified after signing (signature validation will fail)
   - Verify file size is reasonable (prevent malicious large files)
   - Scan for malware/viruses

**Fraud Prevention:**
- Text comparison mismatch → Content was altered between download and signing
- Content hash mismatch → Text was tampered with
- UUID mismatch → Wrong petition document
- Missing/invalid signature → Not properly signed via Gov.br
- Signature validation fails → Document modified after signing
- CPF mismatch (form vs signature) → Fraudulent submission
- Duplicate CPF → Already signed this petition
- File type mismatch → Not a valid PDF

**Technical Implementation:**
- Use **pdfplumber** or **PyPDF2** to extract text content
- Use **pyHanko** or **endesive** to validate PDF digital signatures
- Use **hashlib** (SHA-256) for content hashing
- Store signature certificate data for audit trail

---

## Success Metrics

### Launch Metrics (First 3 Months)

- **Adoption:** 10+ petitions created
- **Engagement:** 100+ total signatures
- **Verification:** >95% automated verification success rate
- **Security:** Zero security incidents
- **Performance:** PDF generation <5 seconds, verification <10 seconds

### Long-Term Metrics (6-12 Months)

- **Growth:** 50+ active petitions
- **Impact:** 5+ petitions reach signature goals
- **Retention:** 30% of signers return to sign additional petitions
- **Quality:** <5% petition content moderation rate
- **Trust:** Gov.br signature adoption >80% of total signatures

---

## Risks and Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Gov.br signature complexity | High | Medium | Provide detailed tutorial, support fallback verification |
| File storage costs | Medium | High | Implement retention policies, compress files |
| PDF verification failures | High | Medium | Manual review queue, clear error messages |
| Performance issues | Medium | Low | Async processing, caching, CDN for downloads |

### Legal/Compliance Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LGPD violations | High | Low | Privacy by design, data minimization, consent flows |
| Fraudulent petitions | Medium | Medium | Moderation queue, user reporting, admin review |
| Signature validity challenges | High | Low | Clear terms of use, proper Gov.br integration |

### User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Signing process too complex | High | High | Step-by-step guide, video tutorials, FAQ |
| Low petition discovery | Medium | Medium | SEO optimization, social sharing, email notifications |
| Mobile usability issues | Medium | Medium | Responsive design, mobile testing |

---

## Timeline Estimate

### Phase-Based Rollout

- **Phase 1-2:** Requirements & Data Models (1 week)
- **Phase 3-4:** PDF Generation & Verification (2 weeks)
- **Phase 5:** User Interface (1 week)
- **Phase 6:** Security & Testing (1 week)
- **Phase 7:** Integration Testing (1 week)
- **Phase 8:** Deployment (3 days)

**Total Estimated Time:** 6-7 weeks for MVP

### MVP Scope

**Included:**
- Basic petition creation (text only)
- PDF generation with hash embedding
- Gov.br signing tutorial
- Upload and automated verification
- Public petition listing
- Basic search/filter

**Deferred to v2:**
- Rich media in petitions (images/videos)
- Advanced analytics
- Email campaigns
- API for third-party integrations
- Petition templates

---

## Next Steps

1. **Review this overview document** with stakeholders
2. **Proceed to Phase 1:** Requirements and Architecture detailed planning
3. **Set up development environment** (new Django app structure)
4. **Research Gov.br signature format** technical specifications
5. **Create initial wireframes** for key user flows

---

## Design Decisions Made

1. ✅ **User Authentication:** 
   - **Petition creation:** Requires user registration and login
   - **Petition signing:** No registration required - open to anyone with Gov.br signature

2. **Verification Form:** After uploading signed PDF, users must fill a form with:
   - Full name
   - CPF (for duplicate detection)
   - Email (for confirmation)
   - System validates this data against the Gov.br signature in the PDF

---

## Open Questions for Discussion

1. **Moderation:** Pre-moderation (review before publication) or post-moderation (publish then review)?
2. **Petition Lifecycle:** Should petitions expire? Auto-close after deadline?
3. **Signature Privacy:** Should signer names be public or private?
4. **File Storage:** Which service for PDF storage on Heroku? (AWS S3, Cloudinary, etc.)
5. **Petition Categories:** What taxonomy for categorizing petitions? (Health, Education, Infrastructure, etc.)
6. **Success Criteria:** What happens when a petition reaches its goal? Automatic delivery to authorities?
7. **Duplicate Prevention:** Should we prevent the same CPF from signing multiple times (even if name differs)?

---

**Document Status:** Ready for review and Phase 1 planning.
