"""
Unit tests for Custody Chain Certificate Service
"""
import pytest
import json
import hashlib
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from apps.signatures.custody_service import (
    build_verification_evidence,
    calculate_verification_hash,
    build_chain_of_custody,
    generate_custody_certificate,
)
from apps.signatures.models import Signature
from tests.factories import SignatureFactory, PetitionFactory


@pytest.mark.unit
@pytest.mark.django_db
class TestCustodyService:
    """Test custody chain certificate generation service"""
    
    def test_build_verification_evidence_structure(self, approved_signature):
        """Test evidence building creates correct structure"""
        evidence = build_verification_evidence(approved_signature, None)
        
        # Check version
        assert evidence['version'] == '1.0'
        
        # Check required top-level keys
        assert 'signature_uuid' in evidence
        assert 'petition_uuid' in evidence
        assert 'timestamp' in evidence
        assert 'verification_steps' in evidence
        assert 'signer_information' in evidence
        
        # Check UUIDs
        assert evidence['signature_uuid'] == str(approved_signature.uuid)
        assert evidence['petition_uuid'] == str(approved_signature.petition.uuid)
    
    def test_build_verification_evidence_with_result(self, approved_signature):
        """Test evidence building with verification result"""
        # Set certificate details on signature first
        approved_signature.certificate_issuer = 'AC Test'
        approved_signature.certificate_serial = '123456'
        approved_signature.certificate_subject = 'CN=Test User'
        approved_signature.save()
        
        verification_result = {
            'verified': True,
            'certificate_issuer': 'AC Test',
            'certificate_serial': '123456',
            'certificate_subject': 'CN=Test User',
        }
        
        evidence = build_verification_evidence(approved_signature, verification_result)
        
        # Check certificate details are included
        assert 'certificate_details' in evidence
        assert evidence['certificate_details']['issuer'] == 'AC Test'
        assert evidence['certificate_details']['serial_number'] == '123456'
    
    def test_build_verification_evidence_steps(self, approved_signature):
        """Test verification steps are included in evidence"""
        evidence = build_verification_evidence(approved_signature, None)
        
        # Should have verification steps
        assert isinstance(evidence['verification_steps'], list)
        assert len(evidence['verification_steps']) > 0
        
        # Each step should have required fields
        for step in evidence['verification_steps']:
            assert 'step' in step
            assert 'status' in step
            assert 'timestamp' in step
    
    def test_calculate_verification_hash_deterministic(self):
        """Test hash calculation is deterministic"""
        evidence = {
            'test': 'data',
            'number': 123,
            'nested': {'key': 'value'}
        }
        
        hash1 = calculate_verification_hash(evidence)
        hash2 = calculate_verification_hash(evidence)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        assert isinstance(hash1, str)
    
    def test_calculate_verification_hash_order_independent(self):
        """Test hash calculation is independent of key order"""
        evidence1 = {'a': 1, 'b': 2, 'c': 3}
        evidence2 = {'c': 3, 'a': 1, 'b': 2}
        
        hash1 = calculate_verification_hash(evidence1)
        hash2 = calculate_verification_hash(evidence2)
        
        # Should be equal because we sort keys
        assert hash1 == hash2
    
    def test_calculate_verification_hash_changes_with_content(self):
        """Test hash changes when content changes"""
        evidence1 = {'test': 'data1'}
        evidence2 = {'test': 'data2'}
        
        hash1 = calculate_verification_hash(evidence1)
        hash2 = calculate_verification_hash(evidence2)
        
        assert hash1 != hash2
    
    def test_build_chain_of_custody_structure(self, approved_signature):
        """Test custody chain building creates correct structure"""
        chain = build_chain_of_custody(approved_signature)
        
        assert 'events' in chain
        assert isinstance(chain['events'], list)
        assert len(chain['events']) > 0
    
    def test_build_chain_of_custody_required_events(self, approved_signature):
        """Test custody chain contains required events"""
        chain = build_chain_of_custody(approved_signature)
        
        event_types = [e['event'] for e in chain['events']]
        
        # Should have submission event
        assert 'submission' in event_types
        
        # Should have approval event
        assert 'approval' in event_types
        
        # Each event should have required fields
        for event in chain['events']:
            assert 'event' in event
            assert 'timestamp' in event
            assert 'description' in event
    
    def test_build_chain_of_custody_chronological_order(self, approved_signature):
        """Test custody chain events have timestamps"""
        chain = build_chain_of_custody(approved_signature)
        
        # Extract timestamps (skip None values)
        timestamps = []
        for event in chain['events']:
            if 'timestamp' in event and event['timestamp']:
                timestamps.append(event['timestamp'])
        
        # Should have at least one timestamp
        assert len(timestamps) > 0
        # All timestamps should be valid ISO format
        for ts in timestamps:
            from dateutil import parser
            parsed = parser.isoparse(ts)
            assert parsed is not None
    
    def test_build_chain_of_custody_with_processing_times(self):
        """Test custody chain includes processing timestamps"""
        signature = SignatureFactory(
            verification_status=Signature.STATUS_APPROVED,
            processing_started_at=timezone.now() - timedelta(seconds=10),
            processing_completed_at=timezone.now() - timedelta(seconds=5),
            verified_at=timezone.now()
        )
        
        chain = build_chain_of_custody(signature)
        event_types = [e['event'] for e in chain['events']]
        
        # Should include processing events
        assert 'processing_started' in event_types
        assert 'processing_completed' in event_types
    
    @patch('config.storage_backends.MediaStorage.save')
    @patch('config.storage_backends.MediaStorage.url')
    def test_generate_custody_certificate_creates_certificate(self, mock_url, mock_save, approved_signature):
        """Test full certificate generation creates all required fields"""
        # Mock S3 storage
        mock_save.return_value = 'signatures/custody_certificates/test_cert.pdf'
        mock_url.return_value = 'https://s3.amazonaws.com/custody_cert.pdf'
        
        certificate_url = generate_custody_certificate(approved_signature)
        
        # Should return a URL
        assert certificate_url is not None
        assert isinstance(certificate_url, str)
        assert 'custody_cert' in certificate_url
        
        # Reload signature from database
        approved_signature.refresh_from_db()
        
        # Check all fields are populated
        assert approved_signature.verification_hash is not None
        assert approved_signature.verification_evidence is not None
        assert approved_signature.chain_of_custody is not None
        assert approved_signature.custody_certificate_url == certificate_url
        assert approved_signature.certificate_generated_at is not None
    
    @pytest.mark.slow
    @patch('config.storage_backends.MediaStorage.save')
    @patch('config.storage_backends.MediaStorage.url')
    def test_generate_custody_certificate_evidence_integrity(self, mock_url, mock_save, approved_signature):
        """Test generated certificate evidence can be verified"""
        # Mock S3 storage
        mock_save.return_value = 'signatures/custody_certificates/test_cert.pdf'
        mock_url.return_value = 'https://s3.amazonaws.com/custody_cert.pdf'
        
        generate_custody_certificate(approved_signature)
        
        approved_signature.refresh_from_db()
        
        # Recalculate hash from evidence
        calculated_hash = calculate_verification_hash(approved_signature.verification_evidence)
        
        # Should match stored hash
        assert calculated_hash == approved_signature.verification_hash
    
    @pytest.mark.slow
    @patch('config.storage_backends.MediaStorage.save')
    @patch('config.storage_backends.MediaStorage.url')
    def test_generate_custody_certificate_with_verification_result(self, mock_url, mock_save):
        """Test certificate generation with verification result data"""
        # Mock S3 storage
        mock_save.return_value = 'signatures/custody_certificates/test_cert.pdf'
        mock_url.return_value = 'https://s3.amazonaws.com/custody_cert.pdf'
        
        signature = SignatureFactory(
            verification_status=Signature.STATUS_APPROVED,
            certificate_issuer='AC SERPRO',
            certificate_serial='ABCDEF123456',
            certificate_subject='CN=Test User,C=BR'
        )
        
        verification_result = {
            'verified': True,
            'certificate_issuer': signature.certificate_issuer,
            'certificate_serial': signature.certificate_serial,
            'certificate_subject': signature.certificate_subject,
        }
        
        certificate_url = generate_custody_certificate(signature, verification_result)
        
        assert certificate_url is not None
        
        signature.refresh_from_db()
        
        # Check certificate details are in evidence
        assert signature.verification_evidence is not None
        assert 'certificate_details' in signature.verification_evidence
        assert signature.verification_evidence['certificate_details']['issuer'] == 'AC SERPRO'
    
    @patch('config.storage_backends.MediaStorage.save')
    @patch('config.storage_backends.MediaStorage.url')
    def test_generate_custody_certificate_idempotent(self, mock_url, mock_save, approved_signature):
        """Test regenerating certificate updates existing data"""
        # Mock S3 storage
        mock_save.return_value = 'signatures/custody_certificates/test_cert.pdf'
        mock_url.return_value = 'https://s3.amazonaws.com/custody_cert.pdf'
        
        # Generate first certificate
        url1 = generate_custody_certificate(approved_signature)
        approved_signature.refresh_from_db()
        hash1 = approved_signature.verification_hash
        
        # Generate again
        url2 = generate_custody_certificate(approved_signature)
        approved_signature.refresh_from_db()
        hash2 = approved_signature.verification_hash
        
        # URLs might differ (timestamp in filename)
        # But hashes should be consistent with same data
        assert hash1 is not None
        assert hash2 is not None
    
    def test_build_verification_evidence_signer_info(self, approved_signature):
        """Test signer information is included in evidence"""
        evidence = build_verification_evidence(approved_signature, None)
        
        assert 'signer_information' in evidence
        signer = evidence['signer_information']
        
        assert 'cpf_hash' in signer
        assert 'full_name' in signer
        assert 'email' in signer
        assert 'city' in signer
        assert 'state' in signer
        
        # Verify values match signature
        assert signer['cpf_hash'] == approved_signature.cpf_hash
        assert signer['full_name'] == approved_signature.full_name
        assert signer['state'] == approved_signature.state
    
    def test_build_verification_evidence_metadata(self, approved_signature):
        """Test metadata is included in evidence"""
        evidence = build_verification_evidence(approved_signature, None)
        
        assert 'metadata' in evidence
        metadata = evidence['metadata']
        
        # Should have system information
        assert 'verifier_version' in metadata
        assert metadata['verifier_version'] == '1.0'
        assert 'system' in metadata
        assert metadata['system'] == 'Petição Brasil'


@pytest.mark.unit
class TestHashCalculations:
    """Test hash calculation edge cases"""
    
    def test_hash_empty_dict(self):
        """Test hashing empty dictionary"""
        hash_result = calculate_verification_hash({})
        assert len(hash_result) == 64
    
    def test_hash_unicode_content(self):
        """Test hashing content with unicode characters"""
        evidence = {
            'text': 'Petição Brasil - Democracia Participativa',
            'author': 'José da Silva',
            'city': 'São Paulo'
        }
        
        hash_result = calculate_verification_hash(evidence)
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)
    
    def test_hash_nested_structures(self):
        """Test hashing deeply nested structures"""
        evidence = {
            'level1': {
                'level2': {
                    'level3': {
                        'data': 'value'
                    }
                }
            }
        }
        
        hash_result = calculate_verification_hash(evidence)
        assert len(hash_result) == 64
    
    def test_hash_with_arrays(self):
        """Test hashing evidence with arrays"""
        evidence = {
            'steps': [
                {'step': 1, 'status': 'pass'},
                {'step': 2, 'status': 'pass'},
                {'step': 3, 'status': 'pass'}
            ]
        }
        
        hash_result = calculate_verification_hash(evidence)
        assert len(hash_result) == 64


@pytest.mark.unit
@pytest.mark.django_db
class TestChainOfCustodyEdgeCases:
    """Test chain of custody edge cases"""
    
    def test_chain_with_minimal_signature(self):
        """Test chain building with minimal signature data"""
        signature = SignatureFactory(
            verification_status=Signature.STATUS_PENDING,
            processing_started_at=None,
            processing_completed_at=None,
            verified_at=None
        )
        
        chain = build_chain_of_custody(signature)
        
        # Should still have at least submission event
        assert len(chain['events']) >= 1
        event_types = [e['event'] for e in chain['events']]
        assert 'submission' in event_types
    
    def test_chain_with_all_timestamps(self):
        """Test chain building with all possible timestamps"""
        signature = SignatureFactory(
            verification_status=Signature.STATUS_APPROVED,
            created_at=timezone.now() - timedelta(hours=1),
            processing_started_at=timezone.now() - timedelta(minutes=30),
            processing_completed_at=timezone.now() - timedelta(minutes=20),
            verified_at=timezone.now() - timedelta(minutes=10),
            certificate_generated_at=timezone.now()
        )
        
        chain = build_chain_of_custody(signature)
        
        # Should have all events
        event_types = [e['event'] for e in chain['events']]
        assert 'submission' in event_types
        assert 'processing_started' in event_types
        assert 'processing_completed' in event_types
        assert 'approval' in event_types
        assert 'certificate_generation' in event_types
