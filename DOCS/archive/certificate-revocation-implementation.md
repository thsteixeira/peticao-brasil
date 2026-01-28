# Certificate Revocation Checking Implementation

**Created:** January 26, 2026  
**Status:** CRITICAL SECURITY GAP  
**Priority:** HIGH

---

## Executive Summary

The current signature verification system does **NOT** check if certificates have been revoked. This is a **critical security and legal compliance gap** that must be addressed.

### Current Gap

The [verification_service.py](../../apps/signatures/verification_service.py) performs:
- ✅ Certificate chain validation
- ✅ Validity period checking (not_before/not_after)
- ✅ Content integrity verification
- ❌ **Revocation status checking (MISSING)**

### Why This Matters

1. **Legal Compliance**: ICP-Brasil DOC-ICP-04 mandates revocation checking
2. **Security**: Prevents acceptance of compromised/fraudulent certificates
3. **Legal Validity**: Without revocation checks, signatures may not hold up in court
4. **Trust**: Users expect that revoked certificates are rejected

---

## Technical Background

### Certificate Revocation Mechanisms

#### 1. CRL (Certificate Revocation List)
- **Format**: X.509 CRL files (DER or PEM encoded)
- **Distribution**: HTTP endpoints published by Certificate Authorities
- **Update frequency**: Periodically (hours to days)
- **Pros**: 
  - Simple to implement
  - Works offline once downloaded
  - Complete list of all revoked certificates
- **Cons**:
  - Can be large (MBs for major CAs)
  - May be stale between updates
  - Requires bandwidth to download

#### 2. OCSP (Online Certificate Status Protocol)
- **Format**: Real-time request/response protocol
- **Method**: Query specific certificate serial number
- **Update frequency**: Real-time
- **Pros**:
  - Always current
  - Smaller bandwidth (only queries needed)
  - Per-certificate granularity
- **Cons**:
  - Requires network connection during validation
  - Can slow down verification
  - Privacy concerns (CA knows which certs you're checking)

### ICP-Brasil Specifics

ICP-Brasil Certificate Authorities publish both:
- **CRL Distribution Points**: URLs in certificate extensions
- **OCSP Responder URLs**: Real-time query endpoints

Example ICP-Brasil CRL endpoints:
```
http://acraiz.icpbrasil.gov.br/LCRacraiz.crl
http://repositorio.serpro.gov.br/lcr/acserpro/acserprov3.crl
http://repositorio.iti.br/lcr/acitiv5/acitiv5.crl
```

---

## Recommended Implementation

### Strategy: OCSP-First with Dynamic CRL Discovery & Caching

**Architecture Decision: Real-time OCSP with Intelligent CRL Fallback**

Priority order for revocation checking:

1. **Cached CRL First** (~10ms): Fastest method using pre-downloaded CRLs from Redis
2. **OCSP Fallback** (2-5s): Real-time check when cached CRL unavailable
3. **Dynamic CRL Discovery** (5-10s): Extract CRL URLs from certificate and download on-demand
4. **Daily CRL Sync**: Background task to refresh cached CRLs from discovered endpoints

```python
Daily Task (3 AM):
1. Download CRLs from previously discovered endpoints
2. Parse and cache in Redis (25-hour TTL)
3. Check for new ICP-Brasil root certificates
4. Prune unused CRL cache entries

Signature Verification (real-time):
1. Extract certificate serial number and issuer info
2. Check cached CRL first (~10ms, instant)
3. If no cached CRL → Try OCSP (2-5s, real-time)
4. If OCSP fails → Extract CRL URL from cert, download & cache (5-10s)
5. Add discovered CRL endpoint to daily sync list
6. Handle failures gracefully based on STRICT mode
```

### Architecture

#### Cached CRL with OCSP and Dynamic Discovery Fallback
```
┌─────────────────────────────────────────────────────────┐
│     Signature Verification (Real-time)                  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Extract Serial Number  │
          │  and Issuer Info        │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Check Cached CRL       │
          │  (~10ms)                │
          └─────────────────────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
          Found CRL           No CRL Cache
              │                   │
              ▼                   ▼
       ┌──────────┐      ┌──────────────┐
       │ Return   │      │ Try OCSP     │
       │ Status   │      │ (2-5s)       │
       └──────────┘      └──────────────┘
                                  │
                        ┌─────────┴─────────┐
                        │                   │
                   Found CRL           No CRL Cache
                        │                   │
                        ▼                   ▼
                 ┌──────────┐      ┌──────────────┐
                 │ Return   │      │ Extract CRL  │
                 │ Status   │      │ URL from Cert│
                 └──────────┘      └──────────────┘
                                           │
                                           ▼
                                  ┌──────────────┐
                                  │ Download CRL │
                                  │ & Cache      │
                                  └──────────────┘
                                           │
                                           ▼
                                  ┌──────────────┐
                                  │ Add to Daily │
                                  │ Sync List    │
                                  └──────────────┘
                                           │
                                           ▼
                                  ┌──────────────┐
                                  │ Return Status│
                                  └──────────────┘

┌─────────────────────────────────────────────────────────┐
│     Daily CRL Refresh Task (3 AM UTC)                   │
│     Celery Beat → Background Task                       │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Load Discovered CRL    │
          │  Endpoints from Cache   │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Download CRL Files     │
          │  (AC-Raiz + discovered) │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Parse & Update Cache   │
          │  TTL: 25 hours          │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Check for New Root     │
          │  Certificates (v14,v15) │
          └─────────────────────────┘
```

#### Real-time Signature Verification Flow
```
┌─────────────────────────────────────────────────────────┐
│         Certificate Validation Flow                     │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Load Certificate       │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Verify Chain & Dates   │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Extract Serial Number  │
          │  and Issuer Info        │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Check Cached CRL       │
          │  (Redis Lookup)         │
          └─────────────────────────┘
                    │         │
              Found │         │   CRL Missing/Stale
                    ▼         └──────┐
          ┌──────────────┐           │
          │ Check Serial │           │
          │ in CRL       │           │
          │ (~10ms)      │           │
          └──────────────┘           │
                    │                │
          Found     │    Not Found   │
                    ▼         ▼      ▼
          ┌─────────────────────────┐
          │  Fallback: Query OCSP   │
          │  (Only if CRL failed)   │
          └─────────────────────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
          Revoked            Not Revoked
              │                   │
              ▼                   ▼
    ┌──────────────┐    ┌──────────────┐
    │ REJECT       │    │ Continue     │
    │ Signature    │    │ Validation   │
    └──────────────┘    └──────────────┘
```

---

## Implementation Details

### 1. Daily CRL Download Task (Celery + Heroku Scheduler)

```python
# apps/signatures/tasks.py

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set

import requests
from celery import shared_task
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def download_and_cache_crls(self):
    """
    Daily task to download all ICP-Brasil CRL files and cache them.
    
    This runs as a scheduled task via Heroku Scheduler.
    Downloads CRLs from all known ICP-Brasil CAs and caches the
    revoked certificate serial numbers in Redis.
    """
    logger.info("Starting daily CRL download task")
    
    # ICP-Brasil CRL Distribution Points
    CRL_ENDPOINTS = {
        'AC-Raiz': 'http://acraiz.icpbrasil.gov.br/LCRacraiz.crl',
        'AC-SERPROv5': 'http://repositorio.serpro.gov.br/lcr/acserpro/acserprov5.crl',
        'AC-Serasa-JUS-v5': 'http://www.serasa.com.br/acjus/lcr/ac-serasa-jus-v5.crl',
        'AC-VALID-v5': 'http://ccd.valid.com.br/lcr/ac-valid-v5.crl',
        'AC-Certisign-G7': 'http://lcr.certisign.com.br/ac-certisign-g7.crl',
        'AC-SOLUTI-v5': 'http://lcr.soluti.com.br/ac-soluti-v5.crl',
        'AC-SINCOR-v5': 'http://repositorio.sincor.com.br/lcr/ac-sincor-v5.crl',
        # Add more ICP-Brasil CAs as needed
    }
    
    results = {
        'success': [],
        'failed': [],
        'total_revoked_certs': 0,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    for ca_name, crl_url in CRL_ENDPOINTS.items():
        try:
            logger.info(f"Downloading CRL for {ca_name} from {crl_url}")
            
            # Download CRL
            response = requests.get(crl_url, timeout=60)
            response.raise_for_status()
            crl_data = response.content
            
            # Parse CRL
            try:
                crl = x509.load_der_x509_crl(crl_data, default_backend())
            except Exception:
                # Try PEM format
                crl = x509.load_pem_x509_crl(crl_data, default_backend())
            
            # Extract revoked certificate serial numbers
            revoked_serials = set()
            revoked_details = {}
            
            for revoked_cert in crl:
                serial = revoked_cert.serial_number
                revoked_serials.add(serial)
                
                # Store additional details
                revoked_details[str(serial)] = {
                    'revocation_date': revoked_cert.revocation_date.isoformat(),
                    'reason': self._get_revocation_reason(revoked_cert),
                }
            
            # Cache in Redis
            cache_key_serials = f"crl:{ca_name}:serials"
            cache_key_details = f"crl:{ca_name}:details"
            cache_key_meta = f"crl:{ca_name}:meta"
            
            # Cache for 25 hours (gives 1-hour overlap before next daily run)
            cache_timeout = 25 * 3600
            
            cache.set(cache_key_serials, revoked_serials, cache_timeout)
            cache.set(cache_key_details, revoked_details, cache_timeout)
            cache.set(cache_key_meta, {
                'this_update': crl.last_update.isoformat(),
                'next_update': crl.next_update.isoformat() if crl.next_update else None,
                'issuer': crl.issuer.rfc4514_string(),
                'count': len(revoked_serials),
                'cached_at': datetime.utcnow().isoformat(),
            }, cache_timeout)
            
            results['success'].append(ca_name)
            results['total_revoked_certs'] += len(revoked_serials)
            
            logger.info(
                f"CRL cached for {ca_name}: {len(revoked_serials)} revoked certificates"
            )
            
        except Exception as e:
            logger.error(f"Failed to download/cache CRL for {ca_name}: {str(e)}")
            results['failed'].append({
                'ca': ca_name,
                'error': str(e)
            })
    
    # Log summary
    logger.info(
        f"CRL download task completed: "
        f"{len(results['success'])} successful, "
        f"{len(results['failed'])} failed, "
        f"{results['total_revoked_certs']} total revoked certificates cached"
    )
    
    return results

def _get_revocation_reason(self, revoked_cert):
    """Extract revocation reason from certificate."""
    try:
        from cryptography.x509.oid import CRLEntryExtensionOID
        reason_ext = revoked_cert.extensions.get_extension_for_oid(
            CRLEntryExtensionOID.CRL_REASON
        )
        return str(reason_ext.value.reason)
    except:
        return 'unspecified'


@shared_task(bind=True, max_retries=3)
def update_icp_brasil_certificates(self):
    """
    Daily task to check for new ICP-Brasil root certificates.
    
    Checks the official ICP-Brasil repository for new root certificates
    and downloads them if they don't already exist locally.
    """
    logger.info("Checking for ICP-Brasil certificate updates")
    
    import os
    import urllib.request
    from django.conf import settings
    
    # ICP-Brasil root certificates (keep updated)
    CERTIFICATE_URLS = {
        'ICP-Brasilv4.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv4.crt',
        'ICP-Brasilv5.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv5.crt',
        'ICP-Brasilv6.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv6.crt',
        'ICP-Brasilv7.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv7.crt',
        'ICP-Brasilv10.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv10.crt',
        'ICP-Brasilv11.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv11.crt',
        'ICP-Brasilv12.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv12.crt',
        'ICP-Brasilv13.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv13.crt',
        # Check periodically for v14, v15, etc.
        'ICP-Brasilv14.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv14.crt',
        'ICP-Brasilv15.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv15.crt',
    }
    
    cert_dir = os.path.join(
        settings.BASE_DIR,
        'apps',
        'signatures',
        'icp_certificates'
    )
    
    os.makedirs(cert_dir, exist_ok=True)
    
    results = {
        'downloaded': [],
        'skipped': [],
        'failed': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    for filename, url in CERTIFICATE_URLS.items():
        filepath = os.path.join(cert_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            results['skipped'].append(filename)
            continue
        
        try:
            logger.info(f"Downloading new ICP-Brasil certificate: {filename}")
            
            with urllib.request.urlopen(url, timeout=30) as response:
                cert_data = response.read()
            
            # Verify it's a valid certificate before saving
            try:
                x509.load_der_x509_certificate(cert_data, default_backend())
            except:
                x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Save certificate
            with open(filepath, 'wb') as f:
                f.write(cert_data)
            
            results['downloaded'].append(filename)
            logger.info(f"Downloaded new certificate: {filename}")
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Certificate doesn't exist yet (future version)
                pass
            else:
                results['failed'].append({
                    'filename': filename,
                    'error': str(e)
                })
        except Exception as e:
            logger.error(f"Failed to download {filename}: {str(e)}")
            results['failed'].append({
                'filename': filename,
                'error': str(e)
            })
    
    if results['downloaded']:
        logger.info(f"Downloaded {len(results['downloaded'])} new ICP-Brasil certificates")
    
    return results
```

### 2. Lightweight CRL Checker Service

```python
# apps/signatures/revocation_checker.py

import logging
from datetime import datetime
from typing import Optional, Dict, Tuple

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import ocsp
from cryptography.x509.oid import ExtensionOID, AuthorityInformationAccessOID
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class RevocationCheckError(Exception):
    """Base exception for revocation checking errors."""
    pass


class CertificateRevocationChecker:
    """
    Check certificate revocation status using cached CRL data.
    
    Primary method: Check against pre-cached CRL data (instant)
    Fallback method: Query OCSP if CRL unavailable (slower)
    """
    
    # Network timeouts (only for OCSP fallback)
    OCSP_TIMEOUT = 10  # seconds
    
    def __init__(self, certificate: x509.Certificate, issuer_certificate: Optional[x509.Certificate] = None):
        """
        Initialize the revocation checker.
        
        Args:
            certificate: The certificate to check
            issuer_certificate: The issuer's certificate (required for OCSP fallback)
        """
        self.certificate = certificate
        self.issuer_certificate = issuer_certificate
        self.serial_number = certificate.serial_number
        
    def is_revoked(self) -> Tuple[bool, Dict]:
        """
        Check if the certificate is revoked.
        
        Returns:
            Tuple of (is_revoked: bool, details: dict)
            
        Raises:
            RevocationCheckError: If unable to determine revocation status
        """
        result = {
            'method': None,
            'checked_at': datetime.utcnow().isoformat(),
            'status': None,
            'reason': None,
            'revocation_date': None,
        }
        
        # Primary method: Check cached CRL
        try:
            is_revoked, crl_details = self._check_cached_crl()
            result.update(crl_details)
            result['method'] = 'CACHED_CRL'
            
            return is_revoked, result
            
        except Exception as e:
            logger.warning(f"Cached CRL check failed, falling back to OCSP: {str(e)}")
        
        # Fallback: OCSP real-time check
        if self.issuer_certificate:
            try:
                is_revoked, ocsp_details = self._check_ocsp()
                result.update(ocsp_details)
                result['method'] = 'OCSP_FALLBACK'
                
                return is_revoked, result
                
            except Exception as e:
                logger.error(f"OCSP fallback also failed: {str(e)}")
        
        # Both methods failed
        if settings.SIGNATURE_VERIFICATION_STRICT:
            # Strict mode: reject if we can't verify
            raise RevocationCheckError(
                "Unable to verify certificate revocation status. "
                f"CRL and OCSP checks both failed."
            )
        else:
            # Permissive mode: allow if we can't verify (log warning)
            logger.warning(
                f"Certificate revocation check failed for serial {self.serial_number}. "
                "Allowing signature due to SIGNATURE_VERIFICATION_STRICT=False. "
                "This is a security risk!"
            )
            result['method'] = 'FAILED'
            result['status'] = 'UNKNOWN'
            result['reason'] = 'Unable to verify - defaulting to not revoked (permissive mode)'
            return False, result
    
    def _check_cached_crl(self) -> Tuple[bool, Dict]:
        """
        Check revocation status against cached CRL data.
        
        Returns:
            Tuple of (is_revoked: bool, details: dict)
        """
        # Determine which CA issued this certificate
        issuer_cn = self._get_issuer_common_name()
        
        # Try to find matching cached CRL
        # We may need to check multiple CAs if issuer is ambiguous
        ca_names = self._get_potential_ca_names(issuer_cn)
        
        for ca_name in ca_names:
            cache_key_serials = f"crl:{ca_name}:serials"
            cache_key_details = f"crl:{ca_name}:details"
            cache_key_meta = f"crl:{ca_name}:meta"
            
            revoked_serials = cache.get(cache_key_serials)
            
            if revoked_serials is not None:
                # Found cached CRL for this CA
                meta = cache.get(cache_key_meta, {})
                
                if self.serial_number in revoked_serials:
                    # Certificate is revoked
                    details_dict = cache.get(cache_key_details, {})
                    cert_details = details_dict.get(str(self.serial_number), {})
                    
                    return True, {
                        'status': 'REVOKED',
                        'revocation_date': cert_details.get('revocation_date'),
                        'reason': cert_details.get('reason', 'unspecified'),
                        'crl_issuer': meta.get('issuer'),
                        'crl_this_update': meta.get('this_update'),
                        'crl_next_update': meta.get('next_update'),
                    }
                else:
                    # Certificate not in CRL (good)
                    return False, {
                        'status': 'GOOD',
                        'crl_issuer': meta.get('issuer'),
                        'crl_this_update': meta.get('this_update'),
                        'crl_next_update': meta.get('next_update'),
                        'revoked_count': meta.get('count', 0),
                    }
        
        # No cached CRL found for this certificate's issuer
        raise RevocationCheckError(
            f"No cached CRL found for certificate issuer: {issuer_cn}"
        )
    
    def _get_issuer_common_name(self) -> str:
        """Extract Common Name from certificate issuer."""
        from cryptography.x509.oid import NameOID
        
        try:
            cn_attrs = self.certificate.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
            if cn_attrs:
                return cn_attrs[0].value
        except:
            pass
        
        return self.certificate.issuer.rfc4514_string()
    
    def _get_potential_ca_names(self, issuer_cn: str) -> list:
        """
        Map certificate issuer to potential cached CRL CA names.
        
        This is needed because the issuer CN in the certificate may not
        exactly match our CRL cache key names.
        """
        # Normalize issuer name
        issuer_lower = issuer_cn.lower()
        
        # Map common ICP-Brasil issuers to our cache keys
        ca_mapping = {
            'serpro': ['AC-SERPROv5'],
            'serasa': ['AC-Serasa-JUS-v5'],
            'valid': ['AC-VALID-v5'],
            'certisign': ['AC-Certisign-G7'],
            'soluti': ['AC-SOLUTI-v5'],
            'sincor': ['AC-SINCOR-v5'],
            'raiz': ['AC-Raiz'],
        }
        
        # Find matching CAs
        potential_cas = []
        for keyword, ca_names in ca_mapping.items():
            if keyword in issuer_lower:
                potential_cas.extend(ca_names)
        
        # Always check AC-Raiz as fallback
        if 'AC-Raiz' not in potential_cas:
            potential_cas.append('AC-Raiz')
        
        return potential_cas
    
    def _check_ocsp(self) -> Tuple[bool, Dict]:
        """
        Fallback: Check revocation status via OCSP.
        
        Only used when cached CRL is unavailable.
        
        Returns:
            Tuple of (is_revoked: bool, details: dict)
        """
        if not self.issuer_certificate:
            raise RevocationCheckError("OCSP requires issuer certificate")
        
        # Extract OCSP URL from certificate
        ocsp_url = self._get_ocsp_url()
        if not ocsp_url:
            raise RevocationCheckError("No OCSP URL found in certificate")
        
        logger.debug(f"Checking OCSP at {ocsp_url}")
        
        # Build OCSP request
        builder = ocsp.OCSPRequestBuilder()
        builder = builder.add_certificate(
            self.certificate,
            self.issuer_certificate,
            hashes.SHA256()
        )
        ocsp_request = builder.build()
        
        # Serialize request
        ocsp_request_bytes = ocsp_request.public_bytes(serialization.Encoding.DER)
        
        # Send OCSP request
        try:
            response = requests.post(
                ocsp_url,
                data=ocsp_request_bytes,
                headers={'Content-Type': 'application/ocsp-request'},
                timeout=self.OCSP_TIMEOUT
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RevocationCheckError(f"OCSP request failed: {str(e)}")
        
        # Parse OCSP response
        ocsp_response = ocsp.load_der_ocsp_response(response.content)
        
        # Check response status
        if ocsp_response.response_status != ocsp.OCSPResponseStatus.SUCCESSFUL:
            raise RevocationCheckError(
                f"OCSP response status: {ocsp_response.response_status}"
            )
        
        # Get certificate status
        cert_status = ocsp_response.certificate_status
        
        details = {
            'status': str(cert_status),
            'this_update': ocsp_response.this_update.isoformat() if ocsp_response.this_update else None,
            'next_update': ocsp_response.next_update.isoformat() if ocsp_response.next_update else None,
        }
        
        if isinstance(cert_status, ocsp.OCSPCertStatus):
            # Certificate is good
            return False, details
        elif isinstance(cert_status, ocsp.RevokedCertStatus):
            # Certificate is revoked
            details['revocation_date'] = cert_status.revocation_time.isoformat()
            details['reason'] = str(cert_status.revocation_reason) if cert_status.revocation_reason else 'unspecified'
            return True, details
        else:
            # Unknown status
            raise RevocationCheckError(f"Unknown OCSP certificate status: {cert_status}")
    
    def _get_ocsp_url(self) -> Optional[str]:
        """Extract OCSP URL from certificate's Authority Information Access extension."""
        try:
            aia_ext = self.certificate.extensions.get_extension_for_oid(
                ExtensionOID.AUTHORITY_INFORMATION_ACCESS
            )
            
            for desc in aia_ext.value:
                if desc.access_method == AuthorityInformationAccessOID.OCSP:
                    return desc.access_location.value
                    
        except x509.ExtensionNotFound:
            pass
        
        return None
```

### 3. Update Celery Beat Schedule

```python
# config/settings/production.py

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'verify-pending-signatures': {
        'task': 'apps.signatures.tasks.verify_pending_signatures',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-expired-petitions': {
        'task': 'apps.petitions.tasks.cleanup_expired_petitions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # NEW: Daily CRL download
    'download-and-cache-crls': {
        'task': 'apps.signatures.tasks.download_and_cache_crls',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    # NEW: Daily ICP-Brasil certificate update check
    'update-icp-brasil-certificates': {
        'task': 'apps.signatures.tasks.update_icp_brasil_certificates',
        'schedule': crontab(hour=3, minute=30),  # Daily at 3:30 AM UTC
    },
}
```

### 4. Create Management Command for Manual Execution

**Location**: `apps/signatures/management/commands/update_crl_and_certificates.py`

**Purpose**: 
- Manual execution for initial setup
- Testing before deploying scheduled tasks
- Emergency updates when needed
- Troubleshooting

**Command**: `python manage.py update_crl_and_certificates`

**Options**:
- `--crl-only`: Only download and cache CRLs
- `--certs-only`: Only check for new ICP-Brasil certificates
- `--force`: Force re-download even if cached

**Implementation**:
- Calls the same Celery tasks (`download_and_cache_crls` and `update_icp_brasil_certificates`)
- Executes synchronously (waits for completion)
- Displays progress and results
- Returns success/failure summary

**Usage Examples**:
```bash
# First-time setup - download everything
python manage.py update_crl_and_certificates

# Only update CRLs
python manage.py update_crl_and_certificates --crl-only

# Only check for new certificates
python manage.py update_crl_and_certificates --certs-only

# On Heroku
heroku run python manage.py update_crl_and_certificates
```

### 5. Deploy Celery Beat Configuration

**No additional dynos needed** - You already have a `beat` dyno running (confirmed from your Heroku setup).

The new CRL download tasks will automatically be picked up by the existing beat worker when you:
1. Update `CELERY_BEAT_SCHEDULE` in production settings (see section 3 above)
2. Deploy the new code to Heroku
3. Restart the beat dyno: `heroku restart beat`

**Verification**:
- Check beat logs: `heroku logs --dyno beat --tail`
- Should see new scheduled tasks registered
- Wait for 3:00 AM UTC to see first execution (or manually trigger for testing)

### 5. Update Verification Service

```python
# apps/signatures/verification_service.py

from apps.signatures.revocation_checker import CertificateRevocationChecker, RevocationCheckError

class PDFSignatureVerifier:
    # ... existing code ...
    
    def _verify_certificate_chain(self, certificate, certificate_chain):
        """
        Verify that the certificate chain leads to an ICP-Brasil root.
        
        Args:
            certificate: The signer's certificate (end entity)
            certificate_chain: Full chain from PKCS#7 (may only include end cert)
        
        Returns:
            bool: True if chain is valid, False otherwise
        """
        # ... existing chain validation code ...
        
        # NEW: Check certificate revocation status
        try:
            # Find issuer certificate in chain for OCSP fallback
            issuer_cert = self._find_issuer_certificate(certificate, certificate_chain)
            
            # Create revocation checker
            revocation_checker = CertificateRevocationChecker(
                certificate=certificate,
                issuer_certificate=issuer_cert
            )
            
            # Check revocation status
            is_revoked, revocation_details = revocation_checker.is_revoked()
            
            # Log the check
            logger.info(
                f"Certificate revocation check for serial {certificate.serial_number}: "
                f"revoked={is_revoked}, method={revocation_details['method']}"
            )
            
            if is_revoked:
                # Certificate is revoked - REJECT
                logger.warning(
                    f"REVOKED certificate detected! Serial: {certificate.serial_number}, "
                    f"Reason: {revocation_details.get('reason')}, "
                    f"Revocation date: {revocation_details.get('revocation_date')}"
                )
                return False
            
        except RevocationCheckError as e:
            # Revocation check failed
            logger.error(f"Revocation check error: {str(e)}")
            
            if settings.SIGNATURE_VERIFICATION_STRICT:
                # Strict mode: reject if we can't verify revocation status
                return False
            else:
                # Permissive mode: allow if we can't verify (with warning)
                logger.warning(
                    "Allowing signature despite revocation check failure "
                    "(SIGNATURE_VERIFICATION_STRICT=False)"
                )
        
        # ... rest of existing validation ...
        return True
    
    def _find_issuer_certificate(self, certificate, certificate_chain):
        """
        Find the issuer's certificate in the chain.
        
        Args:
            certificate: Certificate whose issuer we're looking for
            certificate_chain: List of certificates from PKCS#7
            
        Returns:
            Issuer certificate or None
        """
        issuer_name = certificate.issuer
        
        for cert in certificate_chain:
            if cert.subject == issuer_name:
                return cert
        
        # Not found in chain - try loaded trusted certs
        for trusted_cert_info in self.trusted_certs:
            trusted_cert = trusted_cert_info['certificate']
            if trusted_cert.subject == issuer_name:
                return trusted_cert
        
        return None
```

### 6. Store Revocation Check Evidence

```python
# apps/signatures/views.py

# When creating verification evidence, include revocation check results:

verification_evidence = {
    # ... existing fields ...
    'revocation_check': {
        'performed': True,
        'method': revocation_details['method'],  # 'CACHED_CRL', 'OCSP_FALLBACK', or 'FAILED'
        'checked_at': revocation_details['checked_at'],
        'is_revoked': is_revoked,
        'status': revocation_details.get('status'),
        'reason': revocation_details.get('reason'),
        'revocation_date': revocation_details.get('revocation_date'),
        'crl_issuer': revocation_details.get('crl_issuer'),
        'crl_this_update': revocation_details.get('crl_this_update'),
        'crl_next_update': revocation_details.get('crl_next_update'),
    }
}
```

---

## Deployment Checklist

### 1. Run Initial Setup

**First-time setup**:
```bash
# Download ICP-Brasil root certificates (if not already done)
python manage.py download_icp_certificates

# Download and cache all CRLs + check for certificate updates
python manage.py update_crl_and_certificates
```

**On Heroku**:
```bash
heroku run python manage.py download_icp_certificates
heroku run python manage.py update_crl_and_certificates
```

This populates Redis cache before enabling revocation checking.

### 2. Install Dependencies

Dependencies already installed in requirements.txt:
- `cryptography>=44.0.0` ✅
- `requests>=2.31.0` ✅

No additional installations needed.

### 3. Update Settings

```python
# .env (production)
SIGNATURE_VERIFICATION_STRICT=True

# .env (development - can be permissive for testing)
SIGNATURE_VERIFICATION_STRICT=False
```

### 4. Configure Redis Cache

Ensure Redis is configured via `REDIS_URL` environment variable (Heroku Redis addon or standalone Redis).

### 5. Test CRL Download

Test the new command before deployment:
```bash
# Local
python manage.py update_crl_and_certificates

# Check Redis contains CRL data
python manage.py shell
>>> from django.core.cache import cache
>>> cache.keys('crl:*')  # Should show multiple keys
>>> cache.get('crl:AC-Raiz:meta')  # Should show metadata
```

### 6. Monitor Performance

Add monitoring for:
- CRL download task success rate
- Cached CRL hit rate
- Average revocation check time (~10ms vs 2-5s)
- Failed revocation checks

### 7. Update Documentation

Update user-facing documentation:
- Explain that revoked certificates are rejected
- Document instant verification (~10ms) with cached CRLs
- Explain network requirements for OCSP fallback

---

## Performance Considerations
        urls = []
        
        try:
            crl_ext = self.certificate.extensions.get_extension_for_oid(
                ExtensionOID.CRL_DISTRIBUTION_POINTS
            )
            
            for dist_point in crl_ext.value:
                if dist_point.full_name:
                    for name in dist_point.full_name:
                        if isinstance(name, x509.UniformResourceIdentifier):
                            urls.append(name.value)
                            
        except x509.ExtensionNotFound:
            pass
        
        return urls
```

### 2. Update Settings

```python
# config/settings/base.py

# Signature Verification Settings
SIGNATURE_VERIFICATION_STRICT = env.bool('SIGNATURE_VERIFICATION_STRICT', default=True)
# If True: Reject signatures if revocation check fails
# If False: Allow signatures if revocation check fails (log warning)

# Revocation Check Timeouts
OCSP_TIMEOUT = 10  # seconds
CRL_TIMEOUT = 30   # seconds

# Cache Settings for Revocation Data
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'peticao_brasil',
        'TIMEOUT': 300,
    }
}
```

### 3. Update Verification Service

```python
# apps/signatures/verification_service.py

from apps.signatures.revocation_checker import CertificateRevocationChecker, RevocationCheckError

class PDFSignatureVerifier:
    # ... existing code ...
    
    def _verify_certificate_chain(self, certificate, certificate_chain):
        """
        Verify that the certificate chain leads to an ICP-Brasil root.
        
        Args:
            certificate: The signer's certificate (end entity)
            certificate_chain: Full chain from PKCS#7 (may only include end cert)
        
        Returns:
            bool: True if chain is valid, False otherwise
        """
        # ... existing chain validation code ...
        
        # NEW: Check certificate revocation status
        try:
            # Find issuer certificate in chain for OCSP
            issuer_cert = self._find_issuer_certificate(certificate, certificate_chain)
            
            # Create revocation checker
            revocation_checker = CertificateRevocationChecker(
                certificate=certificate,
                issuer_certificate=issuer_cert
            )
            
            # Check revocation status
            is_revoked, revocation_details = revocation_checker.is_revoked()
            
            # Log the check
            logger.info(
                f"Certificate revocation check for serial {certificate.serial_number}: "
                f"revoked={is_revoked}, method={revocation_details['method']}, "
                f"cached={revocation_details.get('cached', False)}"
            )
            
            if is_revoked:
                # Certificate is revoked - REJECT
                logger.warning(
                    f"REVOKED certificate detected! Serial: {certificate.serial_number}, "
                    f"Reason: {revocation_details.get('reason')}, "
                    f"Revocation date: {revocation_details.get('revocation_date')}"
                )
                return False
            
        except RevocationCheckError as e:
            # Revocation check failed
            logger.error(f"Revocation check error: {str(e)}")
            
            if settings.SIGNATURE_VERIFICATION_STRICT:
                # Strict mode: reject if we can't verify revocation status
                return False
            else:
                # Permissive mode: allow if we can't verify (with warning)
                logger.warning(
                    "Allowing signature despite revocation check failure "
                    "(SIGNATURE_VERIFICATION_STRICT=False)"
                )
        
        # ... rest of existing validation ...
        return True
    
    def _find_issuer_certificate(self, certificate, certificate_chain):
        """
        Find the issuer's certificate in the chain.
        
        Args:
            certificate: Certificate whose issuer we're looking for
            certificate_chain: List of certificates from PKCS#7
            
        Returns:
            Issuer certificate or None
        """
        issuer_name = certificate.issuer
        
        for cert in certificate_chain:
            if cert.subject == issuer_name:
                return cert
        
        # Not found in chain - try loaded trusted certs
        for trusted_cert_info in self.trusted_certs:
            trusted_cert = trusted_cert_info['certificate']
            if trusted_cert.subject == issuer_name:
                return trusted_cert
        
        return None
```

### 4. Store Revocation Check Evidence

```python
# apps/signatures/views.py

# When creating verification evidence, include revocation check results:

verification_evidence = {
    # ... existing fields ...
    'revocation_check': {
        'performed': True,
        'method': revocation_details['method'],  # 'OCSP', 'CRL', or 'FAILED'
        'checked_at': revocation_details['checked_at'],
        'is_revoked': is_revoked,
        'status': revocation_details.get('status'),
        'reason': revocation_details.get('reason'),
        'revocation_date': revocation_details.get('revocation_date'),
        'cached': revocation_details.get('cached', False),
        'crl_url': revocation_details.get('crl_url'),
        'ocsp_url': revocation_details.get('ocsp_url'),
    }
}
```

---

## Deployment Checklist

### 1. Install Dependencies

```bash
# cryptography library already installed (requirements.txt)
# Verify version supports OCSP:
pip install cryptography>=41.0.0

# Ensure requests is installed
pip install requests>=2.31.0
```

### 2. Update Settings

```python
# .env (production)
SIGNATURE_VERIFICATION_STRICT=True

# .env (development - can be permissive for testing)
SIGNATURE_VERIFICATION_STRICT=False
```

### 3. Configure Redis Cache

Ensure Redis is configured for caching CRL/OCSP responses:

```python
# Heroku Redis addon or standalone Redis
REDIS_URL=redis://...
```

### 4. Test Revocation Checking

Create test cases:
- Valid certificate (not revoked)
- Revoked certificate
- Certificate without CRL/OCSP URLs
- Network timeout scenarios
- Cached vs. fresh checks

### 5. Monitor Performance

Add monitoring for:
- Average revocation check time
- Cache hit rate
- Failed revocation checks
- OCSP vs. CRL usage

### 6. Update Documentation

Update user-facing documentation:
- Explain that revoked certificates are rejected
- Document the ~5-10 second additional verification time
- Explain network requirements

---

## Performance Considerations

### Expected Impact with Daily CRL Pre-fetching

**Standard Verification (99.9% of requests):**
- Additional time: ~5-10ms (Redis lookup of serial number in cached CRL)
- Network calls: 0
- User experience: No perceptible delay

**OCSP Fallback (0.1% of requests):**
- Only triggered when CRL cache is unavailable or stale
- Additional time: ~2-5 seconds
- Network calls: 1 (OCSP query)

**Daily Background Task:**
- Runs at 3:00 AM UTC (off-peak hours)
- Downloads all ICP-Brasil CRLs (~5-10 MB total)
- Parses and caches in Redis
- Duration: ~2-5 minutes
- No impact on user-facing requests

### Optimization Strategies

1. **Pre-cached CRL Data**: Daily download eliminates real-time CRL fetching
2. **Redis Storage**: In-memory cache for instant serial number lookups
3. **25-hour Cache TTL**: Provides 1-hour overlap before next daily run
4. **OCSP Fallback**: Only used when cached CRL unavailable
5. **Heroku Scheduler**: Runs during low-traffic hours (3 AM UTC)

---

## Security Considerations

### Strict vs. Permissive Mode

**Strict Mode (`SIGNATURE_VERIFICATION_STRICT=True`):**
- ✅ Maximum security
- ✅ Compliance with ICP-Brasil requirements
- ❌ May reject valid signatures during network outages
- ❌ Slightly lower user acceptance rate

**Permissive Mode (`SIGNATURE_VERIFICATION_STRICT=False`):**
- ✅ Better availability during network issues
- ✅ Higher user acceptance rate
- ❌ May accept revoked certificates (if check fails)
- ❌ Non-compliant with strict ICP-Brasil requirements

**Recommendation**: Use **Strict Mode** in production for legal validity.

### Privacy

OCSP queries reveal which certificates you're validating to the CA. This is generally acceptable for a petition platform, but be aware of the privacy implications.

---

## Testing Plan

### Unit Tests

**File**: `tests/test_revocation_checker.py`

Test cases needed:
1. **Cached CRL check for valid certificate** - Should return not revoked
2. **Cached CRL check for revoked certificate** - Should return revoked with details
3. **OCSP fallback when CRL unavailable** - Should use OCSP successfully
4. **Cache hit verification** - Second check should use cached data
5. **Invalid/missing CRL handling** - Should fallback gracefully
6. **Strict mode enforcement** - Should reject when verification fails
7. **Permissive mode behavior** - Should allow with warning when verification fails

### Integration Tests

**File**: `tests/test_signature_verification_with_revocation.py`

Test scenarios:
1. **Signature with valid certificate** - Should be accepted
2. **Signature with revoked certificate** - Should be rejected
3. **Signature when CRL cache is available** - Fast verification
4. **Signature when CRL cache is stale** - Fallback to OCSP
5. **Network failure handling** - Respect strict/permissive mode
6. **Verification evidence logging** - Ensure revocation check data stored

### CRL Download Task Tests

Test cases:
1. **Successful CRL download** - All CAs downloaded and cached
2. **Partial failure** - Some CAs fail, others succeed
3. **Redis caching** - Verify keys, TTL, data structure
4. **Parse CRL correctly** - Extract serial numbers and metadata
5. **Certificate update check** - Download only new certificates

---

## Rollout Plan

### Phase 1: Development & Testing (1 week)
1. Implement `CertificateRevocationChecker` class
2. Add unit tests
3. Test with real ICP-Brasil certificates
4. Verify OCSP and CRL endpoints work

### Phase 2: Staging Deployment (1 week)
1. Deploy to staging with `SIGNATURE_VERIFICATION_STRICT=False`
2. Monitor logs for revocation check failures
3. Measure performance impact
4. Test with production-like traffic

### Phase 3: Production Deployment (Gradual)
1. Week 1: Deploy with `SIGNATURE_VERIFICATION_STRICT=False`
2. Week 2: Monitor revocation check success rate (target >95%)
3. Week 3: Enable strict mode `SIGNATURE_VERIFICATION_STRICT=True`
4. Week 4: Monitor rejection rates and user feedback

### Phase 4: Monitoring & Optimization (Ongoing)
1. Track cache hit rates
2. Optimize timeouts based on real data
3. Add alerting for high failure rates
4. Update CRL/OCSP endpoints as needed

---

## References

### ICP-Brasil Documentation
- **DOC-ICP-04**: Requisitos Mínimos para Políticas de Certificados
- **DOC-ICP-05**: Política de Certificados da AC Raiz
- [ICP-Brasil Official Site](https://www.gov.br/iti/pt-br/assuntos/icp-brasil)

### Technical Standards
- **RFC 5280**: X.509 Certificate and CRL Profile
- **RFC 6960**: Online Certificate Status Protocol (OCSP)
- **RFC 8954**: OCSP Nonce Extension

### Python Libraries
- [cryptography library - OCSP](https://cryptography.io/en/latest/x509/ocsp/)
- [cryptography library - CRL](https://cryptography.io/en/latest/x509/reference/#x-509-crl-certificate-revocation-list-object)

---

## FAQ

**Q: Will this slow down signature verification?**  
A: First check: ~5-10 seconds. Subsequent checks: ~50ms (cached).

**Q: What if the OCSP/CRL server is down?**  
A: In permissive mode, we allow the signature with a warning. In strict mode, we reject it.

**Q: How often are CRLs updated?**  
A: Typically every 6-24 hours for ICP-Brasil CAs.

**Q: Can we validate old signatures?**  
A: We validate against revocation status at time of check, not signature creation time. For historical accuracy, we'd need archived CRLs (advanced feature).

**Q: Does this affect already-approved signatures?**  
A: No. Revocation checking applies only to new signature submissions.

**Q: What about performance during high traffic?**  
A: Redis caching ensures that repeat checks are instant. Only first-time certificate checks hit the network.

---

## Conclusion

Implementing certificate revocation checking is **essential for legal validity and security** of the petition platform. The hybrid OCSP+CRL approach with caching provides a balance between security, performance, and availability.

**Recommendation**: Implement this in the next sprint as a **high-priority security fix**.
