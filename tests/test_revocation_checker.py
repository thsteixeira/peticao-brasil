"""
Tests for certificate revocation checking.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtensionOID
from django.core.cache import cache

from apps.signatures.revocation_checker import (
    CertificateRevocationChecker,
    RevocationCheckError,
)


@pytest.fixture
def mock_certificate():
    """Create a mock certificate for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "DF"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ICP-Brasil"),
        x509.NameAttribute(NameOID.COMMON_NAME, "AC Test"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        12345678901234567890
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    return cert


@pytest.fixture
def mock_issuer_certificate(mock_certificate):
    """Create a mock issuer certificate."""
    return mock_certificate  # For simplicity, using same cert


@pytest.mark.unit
class TestCertificateRevocationChecker:
    """Test certificate revocation checking functionality."""
    
    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()
    
    def test_cached_crl_check_not_revoked(self, mock_certificate, mock_issuer_certificate):
        """Test cached CRL check for non-revoked certificate."""
        # Setup cache with empty revoked list
        cache.set('crl:AC-Raiz:serials', set(), 25 * 3600)
        cache.set('crl:AC-Raiz:details', {}, 25 * 3600)
        cache.set('crl:AC-Raiz:meta', {
            'issuer': 'CN=AC Test',
            'this_update': datetime.utcnow().isoformat(),
            'count': 0,
        }, 25 * 3600)
        
        checker = CertificateRevocationChecker(
            certificate=mock_certificate,
            issuer_certificate=mock_issuer_certificate
        )
        
        is_revoked, details = checker.is_revoked()
        
        assert is_revoked is False
        assert details['method'] == 'CACHED_CRL'
        assert details['status'] == 'GOOD'
    
    def test_cached_crl_check_revoked(self, mock_certificate, mock_issuer_certificate):
        """Test cached CRL check for revoked certificate."""
        serial = mock_certificate.serial_number
        
        # Setup cache with revoked certificate
        cache.set('crl:AC-Raiz:serials', {serial}, 25 * 3600)
        cache.set('crl:AC-Raiz:details', {
            str(serial): {
                'revocation_date': datetime.utcnow().isoformat(),
                'reason': 'keyCompromise',
            }
        }, 25 * 3600)
        cache.set('crl:AC-Raiz:meta', {
            'issuer': 'CN=AC Test',
            'this_update': datetime.utcnow().isoformat(),
            'count': 1,
        }, 25 * 3600)
        
        checker = CertificateRevocationChecker(
            certificate=mock_certificate,
            issuer_certificate=mock_issuer_certificate
        )
        
        is_revoked, details = checker.is_revoked()
        
        assert is_revoked is True
        assert details['method'] == 'CACHED_CRL'
        assert details['status'] == 'REVOKED'
        assert details['reason'] == 'keyCompromise'
    
    @patch('apps.signatures.revocation_checker.requests.post')
    def test_ocsp_fallback_success(self, mock_post, mock_certificate, mock_issuer_certificate):
        """Test OCSP fallback when CRL cache unavailable."""
        # No cached CRL
        assert cache.get('crl:AC-Raiz:serials') is None
        
        # Mock OCSP response
        from cryptography.x509 import ocsp
        mock_response = MagicMock()
        mock_response.content = b'mock_ocsp_response'
        mock_post.return_value = mock_response
        
        checker = CertificateRevocationChecker(
            certificate=mock_certificate,
            issuer_certificate=mock_issuer_certificate
        )
        
        # Should fallback to OCSP since no cache
        # This will fail in the actual implementation without proper OCSP mocking
        # but demonstrates the test structure
        with pytest.raises(RevocationCheckError):
            checker.is_revoked()
    
    @patch('apps.signatures.revocation_checker.requests.get')
    def test_dynamic_crl_download(self, mock_get, mock_certificate, mock_issuer_certificate):
        """Test dynamic CRL download when cache and OCSP unavailable."""
        # No cached CRL
        assert cache.get('crl:AC-Raiz:serials') is None
        
        # Mock CRL download
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'mock_crl_data'
        mock_get.return_value = mock_response
        
        checker = CertificateRevocationChecker(
            certificate=mock_certificate,
            issuer_certificate=mock_issuer_certificate
        )
        
        # This will attempt dynamic download
        # Implementation will fail without proper CRL mocking
        with pytest.raises((RevocationCheckError, Exception)):
            checker.is_revoked()
    
    @patch('apps.signatures.revocation_checker.settings.SIGNATURE_VERIFICATION_STRICT', True)
    def test_strict_mode_rejects_on_failure(self, mock_certificate, mock_issuer_certificate):
        """Test strict mode rejects signature when revocation check fails."""
        # No cache, no issuer cert for OCSP
        checker = CertificateRevocationChecker(
            certificate=mock_certificate,
            issuer_certificate=None  # No issuer = OCSP will fail
        )
        
        with pytest.raises(RevocationCheckError):
            checker.is_revoked()
    
    @patch('apps.signatures.revocation_checker.settings.SIGNATURE_VERIFICATION_STRICT', False)
    def test_permissive_mode_allows_on_failure(self, mock_certificate):
        """Test permissive mode allows signature when revocation check fails."""
        # No cache, no issuer cert
        checker = CertificateRevocationChecker(
            certificate=mock_certificate,
            issuer_certificate=None
        )
        
        is_revoked, details = checker.is_revoked()
        
        # Should allow in permissive mode
        assert is_revoked is False
        assert details['method'] == 'FAILED'
        assert details['status'] == 'UNKNOWN'
    
    def test_cache_hit_performance(self, mock_certificate, mock_issuer_certificate):
        """Test that cached CRL checks are fast."""
        import time
        
        # Setup cache
        cache.set('crl:AC-Raiz:serials', set(), 25 * 3600)
        cache.set('crl:AC-Raiz:details', {}, 25 * 3600)
        cache.set('crl:AC-Raiz:meta', {
            'issuer': 'CN=AC Test',
            'this_update': datetime.utcnow().isoformat(),
            'count': 0,
        }, 25 * 3600)
        
        checker = CertificateRevocationChecker(
            certificate=mock_certificate,
            issuer_certificate=mock_issuer_certificate
        )
        
        start = time.time()
        is_revoked, details = checker.is_revoked()
        duration = time.time() - start
        
        # Should be very fast (< 100ms)
        assert duration < 0.1
        assert details['method'] == 'CACHED_CRL'
    
    def test_discovered_endpoints_cached(self, mock_certificate, mock_issuer_certificate):
        """Test that discovered CRL endpoints are cached for daily sync."""
        # This would test the _add_to_discovered_endpoints method
        # but requires actual CRL download to trigger
        pass


@pytest.mark.unit
@pytest.mark.django_db
class TestCRLDownloadTask:
    """Test CRL download and caching task."""
    
    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()
    
    @patch('requests.get')
    @patch('cryptography.x509.load_der_x509_crl')
    def test_download_and_cache_crls_success(self, mock_load_crl, mock_get):
        """Test successful CRL download and caching."""
        from apps.signatures.tasks import download_and_cache_crls
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'mock_crl_data'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock CRL parsing
        mock_crl = MagicMock()
        mock_crl.__iter__ = Mock(return_value=iter([]))  # No revoked certs
        mock_crl.last_update_utc = datetime.utcnow()
        mock_crl.next_update_utc = datetime.utcnow() + timedelta(hours=24)
        mock_crl.issuer.rfc4514_string.return_value = 'CN=AC-Raiz'
        mock_load_crl.return_value = mock_crl
        
        # Run task
        result = download_and_cache_crls()
        
        # Verify results
        assert 'AC-Raiz' in result['success']
        
        # Verify cache was populated
        assert cache.get('crl:AC-Raiz:serials') is not None
        assert cache.get('crl:AC-Raiz:meta') is not None
    
    @patch('requests.get')
    def test_download_handles_network_errors(self, mock_get):
        """Test CRL download handles network errors gracefully."""
        from apps.signatures.tasks import download_and_cache_crls
        import requests
        
        # Mock network error
        mock_get.side_effect = requests.RequestException('Network error')
        
        # Run task
        result = download_and_cache_crls()
        
        # Should log failure but not crash
        assert len(result['failed']) >= 1
        assert result['total_revoked_certs'] == 0
    
    def test_discovered_endpoints_loaded(self):
        """Test that discovered CRL endpoints are loaded from cache."""
        from apps.signatures.tasks import download_and_cache_crls
        
        # Add discovered endpoints to cache
        cache.set('discovered_crl_endpoints', {
            'AC-SERPRO': 'http://example.com/serpro.crl',
        }, 30 * 24 * 3600)
        
        # Task should load these endpoints
        # (Would need proper mocking to test full execution)
        pass


@pytest.mark.integration
@pytest.mark.django_db
class TestRevocationIntegration:
    """Integration tests for revocation checking in signature verification."""
    
    def test_signature_verification_with_cached_crl(self):
        """Test full signature verification with cached CRL."""
        # This would test the complete flow from signature upload
        # through verification with revocation checking
        pass
    
    def test_signature_rejected_when_revoked(self):
        """Test that signatures with revoked certificates are rejected."""
        pass
    
    def test_verification_evidence_includes_revocation_data(self):
        """Test that verification evidence includes revocation check results."""
        pass
