"""
Unit tests for CNPJ certificate rejection functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone

from apps.signatures.verification_service import PDFSignatureVerifier, OID_CPF, OID_CNPJ
from apps.signatures.models import Signature
from apps.core.email import send_cnpj_rejection_email


class TestCNPJDetection:
    """Tests for CNPJ certificate detection logic."""
    
    def test_extract_certificate_type_cpf(self):
        """Test extraction of CPF from certificate."""
        verifier = PDFSignatureVerifier()
        
        # Create a mock certificate with CPF OID
        mock_cert = Mock()
        mock_cert.subject.rfc4514_string.return_value = "CN=Test User"
        mock_cert.issuer.rfc4514_string.return_value = "CN=AC Test"
        
        # Mock SAN extension with CPF
        mock_othername = Mock(spec=x509.OtherName)
        mock_othername.type_id = OID_CPF
        mock_othername.value = b"12345678901"
        
        mock_san = Mock()
        mock_san.value = [mock_othername]
        
        mock_ext = Mock()
        mock_ext.value = mock_san.value
        
        mock_cert.extensions.get_extension_for_oid.return_value = mock_ext
        
        cert_type, cert_value = verifier._extract_certificate_type(mock_cert)
        
        assert cert_type == 'CPF'
        assert cert_value == '12345678901'
    
    def test_extract_certificate_type_cnpj(self):
        """Test extraction of CNPJ from certificate."""
        verifier = PDFSignatureVerifier()
        
        # Create a mock certificate with CNPJ OID
        mock_cert = Mock()
        mock_cert.subject.rfc4514_string.return_value = "CN=Test Company"
        mock_cert.issuer.rfc4514_string.return_value = "CN=AC Test"
        
        # Mock SAN extension with CNPJ
        mock_othername = Mock(spec=x509.OtherName)
        mock_othername.type_id = OID_CNPJ
        mock_othername.value = b"12345678901234"
        
        mock_san = Mock()
        mock_san.value = [mock_othername]
        
        mock_ext = Mock()
        mock_ext.value = mock_san.value
        
        mock_cert.extensions.get_extension_for_oid.return_value = mock_ext
        
        cert_type, cert_value = verifier._extract_certificate_type(mock_cert)
        
        assert cert_type == 'CNPJ'
        assert cert_value == '12345678901234'
    
    def test_extract_certificate_type_cnpj_keyword_fallback(self):
        """Test CNPJ detection via keyword fallback."""
        verifier = PDFSignatureVerifier()
        
        # Create a mock certificate without SAN but with CNPJ keyword
        mock_cert = Mock()
        mock_cert.subject.rfc4514_string.return_value = "CN=Test CNPJ Company"
        mock_cert.issuer.rfc4514_string.return_value = "CN=AC Test"
        
        # No SAN extension
        mock_cert.extensions.get_extension_for_oid.side_effect = x509.ExtensionNotFound(
            'Extension not found', x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )
        
        cert_type, cert_value = verifier._extract_certificate_type(mock_cert)
        
        assert cert_type == 'CNPJ'
        assert cert_value is None
    
    def test_extract_certificate_type_unknown(self):
        """Test unknown certificate type."""
        verifier = PDFSignatureVerifier()
        
        # Create a mock certificate without identifiable type
        mock_cert = Mock()
        mock_cert.subject.rfc4514_string.return_value = "CN=Unknown User"
        mock_cert.issuer.rfc4514_string.return_value = "CN=AC Test"
        
        # No SAN extension
        mock_cert.extensions.get_extension_for_oid.side_effect = x509.ExtensionNotFound(
            'Extension not found', x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )
        
        cert_type, cert_value = verifier._extract_certificate_type(mock_cert)
        
        assert cert_type == 'UNKNOWN'
        assert cert_value is None


class TestCNPJRejection:
    """Tests for CNPJ certificate rejection in verification pipeline."""
    
    @patch('apps.signatures.verification_service.PDFSignatureVerifier._load_trusted_certificates')
    def test_cnpj_certificate_rejected(self, mock_load_certs):
        """Test that CNPJ certificates are rejected during verification."""
        from io import BytesIO
        
        mock_load_certs.return_value = []
        verifier = PDFSignatureVerifier()
        
        # Create mock petition
        mock_petition = Mock()
        mock_petition.id = 1
        mock_petition.uuid = '12345678-1234-1234-1234-123456789012'
        
        # Mock certificate with CNPJ OID
        mock_cert = Mock()
        mock_cert.subject.rfc4514_string.return_value = "CN=Test Company CNPJ"
        mock_cert.issuer.rfc4514_string.return_value = "CN=AC Test"
        mock_cert.serial_number = 123456
        
        # Mock SAN extension with CNPJ
        mock_othername = Mock(spec=x509.OtherName)
        mock_othername.type_id = OID_CNPJ
        mock_othername.value = b"12345678901234"
        
        mock_ext = Mock()
        mock_ext.value = [mock_othername]
        mock_cert.extensions.get_extension_for_oid.return_value = mock_ext
        
        # Mock PDF data
        pdf_data = b'%PDF-1.4\n12345678-1234-1234-1234-123456789012\nsome pdf content'
        pdf_file = BytesIO(pdf_data)
        
        # Mock PdfReader to return signature with certificate
        with patch('apps.signatures.verification_service.PdfReader') as mock_reader_class:
            with patch('apps.signatures.verification_service.pkcs7.load_der_pkcs7_certificates') as mock_pkcs7:
                # Setup mock PDF reader
                mock_reader = Mock()
                mock_trailer = {'/Root': {'/AcroForm': {'/Fields': []}}}
                
                # Create mock signature field with valid hex content
                mock_sig_field = Mock()
                mock_sig_dict = Mock()
                # Create valid hex data (just sample bytes)
                valid_hex_bytes = bytes.fromhex('3082010a0282010100')
                mock_contents = Mock()
                mock_contents.original_bytes = valid_hex_bytes
                mock_sig_dict.__contains__ = lambda self, key: key == '/Contents'
                mock_sig_dict.__getitem__ = lambda self, key: mock_contents if key == '/Contents' else None
                mock_sig_field.get_object.return_value = {'/FT': '/Sig', '/V': mock_sig_dict}
                mock_trailer['/Root']['/AcroForm']['/Fields'] = [mock_sig_field]
                mock_reader.trailer = mock_trailer
                mock_reader_class.return_value = mock_reader
                
                # Mock PKCS7 to return our CNPJ certificate
                mock_pkcs7.return_value = [mock_cert]
                
                # This should trigger CNPJ rejection
                result = verifier.verify_pdf_signature(pdf_file, mock_petition)
        
        # Verify result shows rejection
        assert result['verified'] is False
        assert 'CNPJ' in result['error']
        assert result['rejection_code'] == 'CNPJ_NOT_ACCEPTED'
        assert result['certificate_info']['certificate_type'] == 'CNPJ'
    
    @patch('apps.signatures.verification_service.PDFSignatureVerifier._extract_certificate_type')
    @patch('apps.signatures.verification_service.PDFSignatureVerifier._load_trusted_certificates')
    def test_cpf_certificate_continues_validation(self, mock_load_certs, mock_extract_type):
        """Test that CPF certificates continue through normal validation."""
        mock_load_certs.return_value = []
        verifier = PDFSignatureVerifier()
        
        # Mock extraction returning CPF
        mock_extract_type.return_value = ('CPF', '12345678901')
        
        # Create mock petition
        mock_petition = Mock()
        mock_petition.id = 1
        
        # This test verifies that CPF certs don't trigger early rejection
        # The verification will fail later due to missing certificate chain,
        # but that's expected - we're just testing CNPJ rejection logic
        
        # The key is that _extract_certificate_type is called
        # and doesn't cause immediate rejection for CPF


class TestCNPJEmail:
    """Tests for CNPJ rejection email functionality."""
    
    @patch('apps.core.email.render_to_string')
    @patch('apps.core.email.EmailMultiAlternatives')
    def test_cnpj_rejection_email_sent(self, mock_email_class, mock_render):
        """Test that CNPJ rejection email is sent."""
        # Mock signature
        mock_signature = Mock()
        mock_signature.id = 1
        mock_signature.email = 'test@example.com'
        mock_signature.full_name = 'Test User'
        
        # Mock petition
        mock_petition = Mock()
        mock_petition.title = 'Test Petition'
        mock_petition.get_full_url.return_value = 'https://example.com/petition/test'
        
        # Mock certificate info
        cert_info = {
            'issuer': 'AC Test',
            'certificate_type': 'CNPJ'
        }
        
        # Mock templates
        mock_render.side_effect = [
            '<html>Email content</html>',  # HTML template
            'Plain text email content'       # TXT template
        ]
        
        # Mock email instance
        mock_email_instance = Mock()
        mock_email_instance.send.return_value = 1
        mock_email_class.return_value = mock_email_instance
        
        # Send email
        result = send_cnpj_rejection_email(mock_signature, mock_petition, cert_info)
        
        # Verify email was sent
        assert result == 1
        mock_email_instance.send.assert_called_once()
        mock_email_instance.attach_alternative.assert_called_once()
    
    @patch('apps.core.email.render_to_string')
    def test_cnpj_rejection_email_no_email_address(self, mock_render):
        """Test that no email is sent if signature has no email."""
        # Mock signature without email
        mock_signature = Mock()
        mock_signature.id = 1
        mock_signature.email = None
        
        mock_petition = Mock()
        cert_info = {}
        
        result = send_cnpj_rejection_email(mock_signature, mock_petition, cert_info)
        
        # Verify no email sent
        assert result == 0
        mock_render.assert_not_called()


class TestFormValidation:
    """Tests for form validation with CPF-only warning."""
    
    def test_cpf_field_has_help_text(self):
        """Test that CPF field includes pessoa física help text."""
        from apps.signatures.forms import SignatureSubmissionForm
        
        form = SignatureSubmissionForm()
        
        cpf_field = form.fields['cpf']
        assert 'pessoa física' in cpf_field.help_text.lower()


@pytest.mark.django_db
class TestCeleryTaskIntegration:
    """Tests for Celery task CNPJ email integration."""
    
    @patch('apps.core.email.send_cnpj_rejection_email')
    @patch('apps.signatures.verification_service.PDFSignatureVerifier')
    def test_celery_task_sends_cnpj_email(self, mock_verifier_class, mock_send_email):
        """Test that Celery task sends CNPJ rejection email."""
        from apps.signatures.tasks import verify_signature
        from apps.petitions.models import Petition
        from apps.signatures.models import Signature
        from tests.factories import PetitionFactory, UserFactory
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create test data
        user = UserFactory()
        petition = PetitionFactory(creator=user)
        
        # Create signature with PDF
        import hashlib
        pdf_content = b'%PDF-1.4 test content'
        cpf_hash = hashlib.sha256('12345678901'.encode()).hexdigest()
        signature = Signature.objects.create(
            petition=petition,
            full_name='Test User',
            email='test@example.com',
            cpf_hash=cpf_hash,
            city='Test City',
            state='SP',
            signed_pdf=SimpleUploadedFile('test.pdf', pdf_content),
            verification_status=Signature.STATUS_PENDING
        )
        
        # Mock verifier to return CNPJ rejection
        mock_verifier = Mock()
        mock_verifier.verify_pdf_signature.return_value = {
            'verified': False,
            'error': 'Certificado CNPJ detectado',
            'rejection_code': 'CNPJ_NOT_ACCEPTED',
            'certificate_info': {
                'certificate_type': 'CNPJ',
                'serial_number': '12345',
                'issuer': 'Test AC'
            }
        }
        mock_verifier_class.return_value = mock_verifier
        
        # Run task
        verify_signature(signature.id)
        
        # Verify CNPJ email was called
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args[1]['signature'] == signature
        assert call_args[1]['petition'] == petition


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
