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

### Strategy: Hybrid CRL + OCSP

```python
1. Extract CRL/OCSP URLs from certificate
2. Try OCSP first (fast, real-time)
   └─> If OCSP fails/unavailable → fallback to CRL
3. Cache results to avoid repeated queries
4. Handle network failures gracefully
```

### Architecture

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
          │  Extract Revocation URLs│
          │  from Certificate       │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Check OCSP?            │
          └─────────────────────────┘
                    │         │
              Yes   │         │   No OCSP URL
                    ▼         └──────┐
          ┌──────────────┐           │
          │ Query OCSP   │           │
          │ Responder    │           │
          └──────────────┘           │
                    │                │
              Success │    Timeout/  │
                      │    Error     │
                      ▼         ▼    ▼
          ┌─────────────────────────┐
          │  Download & Parse CRL   │
          └─────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │  Check Serial Number    │
          │  in CRL/OCSP Response   │
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

### 1. New Service Class: `CertificateRevocationChecker`

```python
# apps/signatures/revocation_checker.py

import hashlib
import logging
from datetime import datetime, timedelta
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
    Check certificate revocation status using CRL and OCSP.
    
    Implements hybrid approach:
    1. Try OCSP first (fast, real-time)
    2. Fallback to CRL if OCSP unavailable
    3. Cache results to minimize network calls
    """
    
    # Cache timeouts
    OCSP_CACHE_TIMEOUT = 3600  # 1 hour
    CRL_CACHE_TIMEOUT = 21600  # 6 hours
    
    # Network timeouts
    OCSP_TIMEOUT = 10  # seconds
    CRL_TIMEOUT = 30   # seconds
    
    def __init__(self, certificate: x509.Certificate, issuer_certificate: Optional[x509.Certificate] = None):
        """
        Initialize the revocation checker.
        
        Args:
            certificate: The certificate to check
            issuer_certificate: The issuer's certificate (required for OCSP)
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
            'cached': False
        }
        
        # Check cache first
        cache_key = self._get_cache_key()
        cached_result = cache.get(cache_key)
        if cached_result:
            cached_result['cached'] = True
            logger.debug(f"Revocation status from cache: {cached_result}")
            return cached_result['is_revoked'], cached_result
        
        # Try OCSP first
        try:
            is_revoked, ocsp_details = self._check_ocsp()
            result.update(ocsp_details)
            result['method'] = 'OCSP'
            result['is_revoked'] = is_revoked
            
            # Cache successful result
            cache.set(cache_key, result, self.OCSP_CACHE_TIMEOUT)
            
            return is_revoked, result
            
        except Exception as e:
            logger.warning(f"OCSP check failed, falling back to CRL: {str(e)}")
        
        # Fallback to CRL
        try:
            is_revoked, crl_details = self._check_crl()
            result.update(crl_details)
            result['method'] = 'CRL'
            result['is_revoked'] = is_revoked
            
            # Cache successful result
            cache.set(cache_key, result, self.CRL_CACHE_TIMEOUT)
            
            return is_revoked, result
            
        except Exception as e:
            logger.error(f"CRL check also failed: {str(e)}")
            
            # Both methods failed
            if settings.SIGNATURE_VERIFICATION_STRICT:
                # Strict mode: reject if we can't verify
                raise RevocationCheckError(
                    "Unable to verify certificate revocation status. "
                    f"OCSP and CRL checks both failed: {str(e)}"
                )
            else:
                # Permissive mode: allow if we can't verify (log warning)
                logger.warning(
                    f"Certificate revocation check failed for serial {self.serial_number}. "
                    "Allowing signature due to SIGNATURE_VERIFICATION_STRICT=False. "
                    "This is a security risk!"
                )
                result['method'] = 'FAILED'
                result['is_revoked'] = False
                result['reason'] = 'Unable to verify - defaulting to not revoked (permissive mode)'
                return False, result
    
    def _get_cache_key(self) -> str:
        """Generate cache key for this certificate."""
        return f"cert_revocation:{self.serial_number}"
    
    def _check_ocsp(self) -> Tuple[bool, Dict]:
        """
        Check revocation status via OCSP.
        
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
    
    def _check_crl(self) -> Tuple[bool, Dict]:
        """
        Check revocation status via CRL.
        
        Returns:
            Tuple of (is_revoked: bool, details: dict)
        """
        # Extract CRL URLs from certificate
        crl_urls = self._get_crl_urls()
        if not crl_urls:
            raise RevocationCheckError("No CRL distribution points found in certificate")
        
        # Try each CRL URL until one works
        last_error = None
        for crl_url in crl_urls:
            try:
                logger.debug(f"Downloading CRL from {crl_url}")
                return self._check_crl_url(crl_url)
            except Exception as e:
                logger.warning(f"CRL check failed for {crl_url}: {str(e)}")
                last_error = e
                continue
        
        # All CRL URLs failed
        raise RevocationCheckError(f"All CRL URLs failed. Last error: {last_error}")
    
    def _check_crl_url(self, crl_url: str) -> Tuple[bool, Dict]:
        """
        Download and check a specific CRL.
        
        Args:
            crl_url: URL of the CRL to download
            
        Returns:
            Tuple of (is_revoked: bool, details: dict)
        """
        # Check if CRL is cached
        crl_cache_key = f"crl:{hashlib.sha256(crl_url.encode()).hexdigest()}"
        crl_data = cache.get(crl_cache_key)
        
        if not crl_data:
            # Download CRL
            try:
                response = requests.get(crl_url, timeout=self.CRL_TIMEOUT)
                response.raise_for_status()
                crl_data = response.content
                
                # Cache the CRL data
                cache.set(crl_cache_key, crl_data, self.CRL_CACHE_TIMEOUT)
                
            except requests.RequestException as e:
                raise RevocationCheckError(f"Failed to download CRL: {str(e)}")
        
        # Parse CRL
        try:
            crl = x509.load_der_x509_crl(crl_data, default_backend())
        except Exception:
            # Try PEM format
            try:
                crl = x509.load_pem_x509_crl(crl_data, default_backend())
            except Exception as e:
                raise RevocationCheckError(f"Failed to parse CRL: {str(e)}")
        
        # Check if our certificate is in the CRL
        revoked_cert = crl.get_revoked_certificate_by_serial_number(self.serial_number)
        
        details = {
            'crl_url': crl_url,
            'crl_this_update': crl.last_update.isoformat(),
            'crl_next_update': crl.next_update.isoformat() if crl.next_update else None,
        }
        
        if revoked_cert:
            # Certificate is revoked
            details['status'] = 'REVOKED'
            details['revocation_date'] = revoked_cert.revocation_date.isoformat()
            
            # Extract revocation reason if available
            try:
                reason_ext = revoked_cert.extensions.get_extension_for_oid(
                    x509.oid.CRLEntryExtensionOID.CRL_REASON
                )
                details['reason'] = str(reason_ext.value.reason)
            except:
                details['reason'] = 'unspecified'
            
            return True, details
        else:
            # Certificate not in CRL (good)
            details['status'] = 'GOOD'
            return False, details
    
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
    
    def _get_crl_urls(self) -> list:
        """Extract CRL URLs from certificate's CRL Distribution Points extension."""
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

### Expected Impact

**With Caching (99% of requests):**
- Additional time: ~50ms (cache lookup)
- Network calls: 0

**Without Cache (1% of requests):**
- OCSP: ~2-5 seconds
- CRL: ~5-15 seconds (depends on CRL size)

### Optimization Strategies

1. **Aggressive Caching**: Cache OCSP responses for 1 hour, CRLs for 6 hours
2. **Async Checks**: Consider background tasks for non-critical validations
3. **Connection Pooling**: Reuse HTTP connections for multiple checks
4. **Fallback Gracefully**: Allow signatures if revocation check fails (with logging)

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

```python
# tests/test_revocation_checker.py

import pytest
from cryptography import x509
from apps.signatures.revocation_checker import CertificateRevocationChecker

def test_ocsp_check_good_certificate():
    """Test OCSP check for valid certificate"""
    # Load test certificate
    cert = load_test_certificate('valid_icp_brasil.crt')
    issuer = load_test_certificate('issuer.crt')
    
    checker = CertificateRevocationChecker(cert, issuer)
    is_revoked, details = checker.is_revoked()
    
    assert is_revoked is False
    assert details['method'] == 'OCSP'
    assert details['status'] == 'GOOD'

def test_crl_check_revoked_certificate():
    """Test CRL check for revoked certificate"""
    cert = load_test_certificate('revoked_icp_brasil.crt')
    
    checker = CertificateRevocationChecker(cert)
    is_revoked, details = checker.is_revoked()
    
    assert is_revoked is True
    assert details['method'] == 'CRL'
    assert 'revocation_date' in details

def test_cache_hit():
    """Test that repeated checks use cache"""
    cert = load_test_certificate('valid_icp_brasil.crt')
    issuer = load_test_certificate('issuer.crt')
    
    checker1 = CertificateRevocationChecker(cert, issuer)
    is_revoked1, details1 = checker1.is_revoked()
    
    checker2 = CertificateRevocationChecker(cert, issuer)
    is_revoked2, details2 = checker2.is_revoked()
    
    assert details2['cached'] is True
```

### Integration Tests

```python
# tests/test_signature_verification_with_revocation.py

def test_reject_revoked_certificate_signature(client, petition):
    """Signatures with revoked certificates should be rejected"""
    # Upload PDF signed with revoked certificate
    # ...
    
    # Should be rejected with specific error
    assert signature.verification_status == 'rejected'
    assert 'revoked' in signature.rejection_reason.lower()
```

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
