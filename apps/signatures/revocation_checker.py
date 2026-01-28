"""
Certificate revocation checking service.
Supports cached CRL checking with OCSP fallback.
"""
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
    Check certificate revocation status with intelligent fallback.
    
    Priority order:
    1. Cached CRL (~10ms) - Fastest, uses pre-downloaded CRL data
    2. OCSP (2-5s) - Real-time when no CRL cache available
    3. Dynamic CRL (5-10s) - Downloads CRL on-demand if both fail
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
        
        Priority:
        1. Cached CRL (~10ms, fastest)
        2. OCSP (2-5s, real-time when no cache)
        3. Dynamic CRL download (5-10s, on-demand discovery)
        
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
        
        # Primary method: Check cached CRL (fastest, ~10ms)
        try:
            is_revoked, crl_details = self._check_cached_crl()
            result.update(crl_details)
            result['method'] = 'CACHED_CRL'
            
            return is_revoked, result
            
        except Exception as e:
            logger.warning(f"Cached CRL check failed, trying OCSP: {str(e)}")
        
        # Fallback 1: OCSP real-time check
        if self.issuer_certificate:
            try:
                is_revoked, ocsp_details = self._check_ocsp()
                result.update(ocsp_details)
                result['method'] = 'OCSP'
                
                return is_revoked, result
                
            except Exception as e:
                logger.warning(f"OCSP check failed, trying dynamic CRL: {str(e)}")
        
        # Fallback 2: Download CRL on-demand
        try:
            is_revoked, dynamic_crl_details = self._download_and_check_crl()
            result.update(dynamic_crl_details)
            result['method'] = 'DYNAMIC_CRL'
            
            return is_revoked, result
            
        except Exception as e:
            logger.error(f"All revocation check methods failed: {str(e)}")
        
        # All methods failed
        if getattr(settings, 'SIGNATURE_VERIFICATION_STRICT', True):
            # Strict mode: reject if we can't verify
            raise RevocationCheckError(
                "Unable to verify certificate revocation status. "
                f"OCSP, cached CRL, and dynamic CRL checks all failed."
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
        ca_names = self._get_potential_ca_names(issuer_cn)
        
        for ca_name in ca_names:
            cache_key_serials = f"crl:{ca_name}:serials"
            cache_key_details = f"crl:{ca_name}:details"
            cache_key_meta = f"crl:{ca_name}:meta"
            
            revoked_serials = cache.get(cache_key_serials)
            
            if revoked_serials is not None:
                # Found cached CRL for this CA
                meta = cache.get(cache_key_meta, {})
                
                logger.info(
                    f"✓ Using cached CRL for {ca_name} "
                    f"(serial: {self.serial_number}, issuer: {issuer_cn})"
                )
                
                if self.serial_number in revoked_serials:
                    # Certificate is revoked
                    details_dict = cache.get(cache_key_details, {})
                    cert_details = details_dict.get(str(self.serial_number), {})
                    
                    logger.warning(
                        f"✗ Certificate REVOKED via CRL: {ca_name} "
                        f"(serial: {self.serial_number})"
                    )
                    
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
                    logger.info(
                        f"✓ Certificate NOT revoked per CRL: {ca_name} "
                        f"(serial: {self.serial_number})"
                    )
                    
                    return False, {
                        'status': 'GOOD',
                        'crl_issuer': meta.get('issuer'),
                        'crl_this_update': meta.get('this_update'),
                        'crl_next_update': meta.get('next_update'),
                        'revoked_count': meta.get('count', 0),
                    }
        
        # No cached CRL found for this certificate's issuer
        logger.info(
            f"⚠ No cached CRL found for issuer: {issuer_cn} "
            f"(serial: {self.serial_number}) - will try OCSP fallback"
        )
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
        
        logger.info(
            f"→ Using OCSP fallback for serial {self.serial_number} at {ocsp_url}"
        )
        
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
            logger.info(
                f"✓ OCSP confirms certificate NOT revoked (serial: {self.serial_number})"
            )
            return False, details
        elif isinstance(cert_status, ocsp.RevokedCertStatus):
            # Certificate is revoked
            logger.warning(
                f"✗ Certificate REVOKED via OCSP (serial: {self.serial_number})"
            )
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
    
    def _get_crl_urls(self) -> list:
        """Extract CRL distribution point URLs from certificate."""
        try:
            crl_ext = self.certificate.extensions.get_extension_for_oid(
                ExtensionOID.CRL_DISTRIBUTION_POINTS
            )
            
            urls = []
            for dp in crl_ext.value:
                if dp.full_name:
                    for name in dp.full_name:
                        if hasattr(name, 'value'):
                            urls.append(name.value)
            return urls
                    
        except x509.ExtensionNotFound:
            pass
        
        return []
    
    def _download_and_check_crl(self) -> Tuple[bool, Dict]:
        """
        Download CRL on-demand from certificate's distribution points.
        Cache the CRL and add endpoint to daily sync list.
        
        Returns:
            Tuple of (is_revoked: bool, details: dict)
        """
        crl_urls = self._get_crl_urls()
        if not crl_urls:
            raise RevocationCheckError("No CRL distribution points found in certificate")
        
        issuer_cn = self._get_issuer_common_name()
        
        logger.info(
            f"📥 Downloading CRL on-demand for {issuer_cn} "
            f"(serial: {self.serial_number})"
        )
        
        # Try each CRL URL until one succeeds
        for crl_url in crl_urls:
            try:
                logger.info(f"Downloading CRL from {crl_url}")
                
                response = requests.get(crl_url, timeout=30)
                response.raise_for_status()
                crl_data = response.content
                
                # Parse CRL
                try:
                    crl = x509.load_der_x509_crl(crl_data, default_backend())
                except Exception:
                    crl = x509.load_pem_x509_crl(crl_data, default_backend())
                
                # Extract revoked serials
                revoked_serials = set()
                revoked_details = {}
                
                for revoked_cert in crl:
                    serial = revoked_cert.serial_number
                    revoked_serials.add(serial)
                    
                    revoked_details[str(serial)] = {
                        'revocation_date': revoked_cert.revocation_date_utc.isoformat(),
                        'reason': self._get_revocation_reason_from_cert(revoked_cert),
                    }
                
                # Cache the CRL (25 hour TTL)
                ca_name = self._normalize_ca_name(issuer_cn)
                cache_key_serials = f"crl:{ca_name}:serials"
                cache_key_details = f"crl:{ca_name}:details"
                cache_key_meta = f"crl:{ca_name}:meta"
                
                cache_timeout = 25 * 3600
                
                cache.set(cache_key_serials, revoked_serials, cache_timeout)
                cache.set(cache_key_details, revoked_details, cache_timeout)
                cache.set(cache_key_meta, {
                    'this_update': crl.last_update_utc.isoformat(),
                    'next_update': crl.next_update_utc.isoformat() if crl.next_update_utc else None,
                    'issuer': crl.issuer.rfc4514_string(),
                    'count': len(revoked_serials),
                    'cached_at': datetime.utcnow().isoformat(),
                }, cache_timeout)
                
                # Add to discovered endpoints for daily sync
                self._add_to_discovered_endpoints(ca_name, crl_url)
                
                logger.info(
                    f"✓ CRL downloaded and cached: {ca_name} "
                    f"({len(revoked_serials)} revoked certificates)"
                )
                
                # Check if this certificate is revoked
                if self.serial_number in revoked_serials:
                    cert_details = revoked_details.get(str(self.serial_number), {})
                    logger.warning(f"✗ Certificate REVOKED via dynamic CRL: {ca_name}")
                    
                    return True, {
                        'status': 'REVOKED',
                        'revocation_date': cert_details.get('revocation_date'),
                        'reason': cert_details.get('reason', 'unspecified'),
                        'crl_url': crl_url,
                    }
                else:
                    logger.info(f"✓ Certificate NOT revoked per dynamic CRL: {ca_name}")
                    
                    return False, {
                        'status': 'GOOD',
                        'crl_url': crl_url,
                        'revoked_count': len(revoked_serials),
                    }
                
            except Exception as e:
                logger.warning(f"Failed to download CRL from {crl_url}: {str(e)}")
                continue
        
        raise RevocationCheckError(
            f"Failed to download CRL from any distribution point: {crl_urls}"
        )
    
    def _normalize_ca_name(self, issuer_cn: str) -> str:
        """Normalize CA name for cache key."""
        # Remove special characters and spaces
        import re
        normalized = re.sub(r'[^a-zA-Z0-9-]', '-', issuer_cn)
        normalized = re.sub(r'-+', '-', normalized)
        return normalized.strip('-')
    
    def _get_revocation_reason_from_cert(self, revoked_cert) -> str:
        """Extract revocation reason from revoked certificate entry."""
        try:
            from cryptography.x509.oid import CRLEntryExtensionOID
            reason_ext = revoked_cert.extensions.get_extension_for_oid(
                CRLEntryExtensionOID.CRL_REASON
            )
            return str(reason_ext.value.reason)
        except:
            return 'unspecified'
    
    def _add_to_discovered_endpoints(self, ca_name: str, crl_url: str):
        """Add discovered CRL endpoint to list for daily sync."""
        cache_key = 'discovered_crl_endpoints'
        endpoints = cache.get(cache_key, {})
        
        if ca_name not in endpoints:
            endpoints[ca_name] = crl_url
            # Cache for 30 days (will be refreshed as new signatures come in)
            cache.set(cache_key, endpoints, 30 * 24 * 3600)
            logger.info(f"Added {ca_name} to discovered CRL endpoints for daily sync")
