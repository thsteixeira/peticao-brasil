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
    
    @patch('apps.petitions.tasks.generate_pdf')
    @patch('apps.petitions.tasks.default_storage')
    def test_generate_petition_pdf_success(self, mock_storage, mock_generate_pdf, petition):
        """Test PDF generation task succeeds"""
        # Mock PDF generation
        mock_generate_pdf.return_value = b'PDF content'
        mock_storage.save.return_value = 'petitions/pdfs/test.pdf'
        
        # Run task
        result = generate_petition_pdf(petition.id)
        
        # Verify task executed
        assert result is not None
        mock_generate_pdf.assert_called_once()
        mock_storage.save.assert_called_once()
        
        # Verify petition was updated
        petition.refresh_from_db()
        assert petition.pdf_file is not None
    
    @patch('apps.petitions.tasks.generate_pdf')
    def test_generate_petition_pdf_failure(self, mock_generate_pdf, petition):
        """Test PDF generation handles errors"""
        # Mock failure
        mock_generate_pdf.side_effect = Exception('PDF generation failed')
        
        # Task should handle exception
        with pytest.raises(Exception):
            generate_petition_pdf(petition.id)


@pytest.mark.unit
@pytest.mark.django_db
class TestSignatureTasks:
    """Test signature verification tasks"""
    
    @patch('apps.signatures.tasks.verify_pkcs7_signature')
    def test_verify_signature_success(self, mock_verify, signature):
        """Test signature verification succeeds"""
        # Mock successful verification
        mock_verify.return_value = True
        
        # Assume signature has certificate_file
        signature.certificate_file = 'signatures/pdfs/test.pdf'
        signature.save()
        
        # Run task
        result = verify_signature(signature.id)
        
        # Verify signature was approved
        signature.refresh_from_db()
        assert signature.verification_status == 'approved'
        assert signature.verified_at is not None
    
    @patch('apps.signatures.tasks.verify_pkcs7_signature')
    def test_verify_signature_invalid(self, mock_verify, signature):
        """Test signature verification fails for invalid signature"""
        # Mock failed verification
        mock_verify.return_value = False
        
        signature.certificate_file = 'signatures/pdfs/test.pdf'
        signature.save()
        
        # Run task
        verify_signature(signature.id)
        
        # Verify signature was rejected
        signature.refresh_from_db()
        assert signature.verification_status == 'rejected'
        assert 'Invalid' in signature.rejection_reason
    
    def test_verify_signature_missing_certificate(self, signature):
        """Test verification fails gracefully without certificate"""
        # Signature without certificate_file
        signature.certificate_file = None
        signature.save()
        
        # Should handle gracefully
        result = verify_signature(signature.id)
        
        signature.refresh_from_db()
        # Should still be pending or rejected
        assert signature.verification_status in ['pending', 'rejected']


@pytest.mark.slow
@pytest.mark.django_db
class TestTaskPerformance:
    """Performance tests for tasks"""
    
    def test_bulk_pdf_generation(self):
        """Test generating PDFs for multiple petitions"""
        petitions = PetitionFactory.create_batch(10)
        
        with patch('apps.petitions.tasks.generate_pdf') as mock_gen:
            mock_gen.return_value = b'PDF'
            
            # Generate PDFs
            for petition in petitions:
                generate_petition_pdf(petition.id)
            
            # Should call generate_pdf 10 times
            assert mock_gen.call_count == 10
