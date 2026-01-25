"""
Tests for Celery tasks
"""
import pytest
from unittest.mock import patch, MagicMock
from apps.petitions.tasks import generate_petition_pdf
from apps.signatures.tasks import verify_signature
from tests.factories import PetitionFactory, SignatureFactory


@pytest.mark.unit
@pytest.mark.django_db
class TestPetitionTasks:
    """Test petition-related Celery tasks"""
    
    @patch('apps.petitions.pdf_service.PetitionPDFGenerator.generate_and_save')
    def test_generate_petition_pdf_success(self, mock_generate_and_save, petition):
        """Test PDF generation task succeeds"""
        # Mock PDF generation
        mock_generate_and_save.return_value = 'petitions/pdfs/test.pdf'
        
        # Run task
        result = generate_petition_pdf(petition.id)
        
        # Verify task executed
        assert result is not None
        assert result['success'] is True
        assert 'petition_uuid' in result
        mock_generate_and_save.assert_called_once()
    
    @patch('apps.petitions.pdf_service.PetitionPDFGenerator.generate_and_save')
    def test_generate_petition_pdf_failure(self, mock_generate_and_save, petition):
        """Test PDF generation handles errors"""
        # Mock failure
        mock_generate_and_save.side_effect = Exception('PDF generation failed')
        
        # Task should handle exception and retry
        with pytest.raises(Exception):
            generate_petition_pdf(petition.id)


@pytest.mark.unit
@pytest.mark.django_db
class TestSignatureTasks:
    """Test signature verification tasks"""
    
    @patch('config.storage_backends.MediaStorage.open')
    @patch('config.storage_backends.MediaStorage.save', return_value='signatures/pdfs/test.pdf')
    @patch('config.storage_backends.MediaStorage.url', return_value='https://test.s3.amazonaws.com/test.pdf')
    @patch('apps.signatures.verification_service.PDFSignatureVerifier.verify_pdf_signature')
    def test_verify_signature_success(self, mock_verify, mock_s3_url, mock_s3_save, mock_s3_open, signature, mock_pdf_file):
        """Test signature verification succeeds"""
        # Mock S3 file open to return mock PDF
        mock_s3_open.return_value = mock_pdf_file
        
        # Mock successful verification
        mock_verify.return_value = {
            'verified': True,
            'certificate_info': {
                'subject': 'CN=Test User',
                'issuer': 'CN=Test CA',
                'serial_number': '12345'
            }
        }
        
        # Assume signature has signed_pdf
        signature.signed_pdf = mock_pdf_file
        signature.save()
        
        # Run task
        result = verify_signature(signature.id)
        
        # Verify signature was approved
        signature.refresh_from_db()
        assert signature.verification_status == 'approved'
        assert signature.verified_at is not None
    
    @patch('config.storage_backends.MediaStorage.open')
    @patch('config.storage_backends.MediaStorage.save', return_value='signatures/pdfs/test.pdf')
    @patch('config.storage_backends.MediaStorage.url', return_value='https://test.s3.amazonaws.com/test.pdf')
    @patch('apps.signatures.verification_service.PDFSignatureVerifier.verify_pdf_signature')
    def test_verify_signature_invalid(self, mock_verify, mock_s3_url, mock_s3_save, mock_s3_open, signature, mock_pdf_file):
        """Test signature verification fails for invalid signature"""
        # Mock S3 file open to return mock PDF
        mock_s3_open.return_value = mock_pdf_file
        
        # Mock failed verification
        mock_verify.return_value = {
            'verified': False,
            'error': 'Invalid signature'
        }
        
        signature.signed_pdf = mock_pdf_file
        signature.save()
        
        # Run task
        verify_signature(signature.id)
        
        # Verify signature was rejected
        signature.refresh_from_db()
        assert signature.verification_status == 'rejected'
        assert signature.verification_notes is not None or signature.verification_notes != ''
    
    def test_verify_signature_missing_certificate(self, signature):
        """Test verification fails gracefully without certificate"""
        # Signature without signed_pdf - the default signature fixture has no file
        assert not signature.signed_pdf.name  # No file attached
        
        # Task should handle the error gracefully by retrying
        # The verification task will raise a retry exception when it can't open the file
        with pytest.raises(Exception):  # Will raise retry exception from Celery
            verify_signature(signature.id)
        
        signature.refresh_from_db()
        # After max retries, should be marked for manual review
        assert signature.verification_status in ['pending', 'manual_review']


@pytest.mark.slow
@pytest.mark.django_db
class TestTaskPerformance:
    """Performance tests for tasks"""
    
    def test_bulk_pdf_generation(self):
        """Test generating PDFs for multiple petitions"""
        petitions = PetitionFactory.create_batch(10)
        
        with patch('apps.petitions.pdf_service.PetitionPDFGenerator.generate_and_save') as mock_gen:
            mock_gen.return_value = 'petitions/pdfs/test.pdf'
            
            # Generate PDFs
            for petition in petitions:
                generate_petition_pdf(petition.id)
                
            # Verify mock was called for each petition
            assert mock_gen.call_count == 10
            
            # Should call generate_pdf 10 times
            assert mock_gen.call_count == 10
