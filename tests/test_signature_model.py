"""
Unit tests for Signature model
"""
import pytest
from django.utils import timezone
from apps.signatures.models import Signature
from tests.factories import SignatureFactory, PetitionFactory


@pytest.mark.unit
@pytest.mark.django_db
class TestSignatureModel:
    """Test Signature model methods and properties"""
    
    def test_signature_creation(self):
        """Test signature can be created"""
        signature = SignatureFactory()
        assert signature.pk is not None
        assert signature.uuid is not None
        assert signature.full_name
    
    def test_signature_str(self):
        """Test signature string representation"""
        petition = PetitionFactory(title="Test Petition")
        signature = SignatureFactory(petition=petition, full_name="João Silva")
        assert "João Silva" in str(signature)
        assert "Test Petition" in str(signature)
    
    def test_cpf_hashing(self):
        """Test CPF hashing function"""
        cpf = "123.456.789-01"
        hash1 = Signature.hash_cpf(cpf)
        hash2 = Signature.hash_cpf("12345678901")  # Same CPF, no formatting
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 char hex string
        assert cpf not in hash1  # Hash should not contain original CPF
    
    def test_ip_hashing(self):
        """Test IP address hashing function"""
        ip = "192.168.1.1"
        hash1 = Signature.hash_ip(ip)
        
        assert len(hash1) == 64
        assert ip not in hash1
    
    def test_display_name_public(self):
        """Test display name when public"""
        signature = SignatureFactory(
            full_name="João Silva",
            display_name_publicly=True
        )
        assert signature.display_name == "João Silva"
    
    def test_display_name_private(self):
        """Test display name when private (initials only)"""
        signature = SignatureFactory(
            full_name="João Silva",
            display_name_publicly=False
        )
        assert signature.display_name == "J. S."
    
    def test_display_name_private_single_name(self):
        """Test display name with single name"""
        signature = SignatureFactory(
            full_name="Madonna",
            display_name_publicly=False
        )
        assert signature.display_name == "M."
    
    def test_is_verified_property(self):
        """Test is_verified property"""
        verified = SignatureFactory(verification_status=Signature.STATUS_APPROVED)
        pending = SignatureFactory(verification_status=Signature.STATUS_PENDING)
        
        assert verified.is_verified is True
        assert pending.is_verified is False
    
    def test_approve_signature(self):
        """Test signature approval method"""
        signature = SignatureFactory(
            verification_status=Signature.STATUS_PENDING
        )
        petition = signature.petition
        initial_count = petition.signature_count
        
        signature.approve()
        signature.refresh_from_db()
        petition.refresh_from_db()
        
        assert signature.verification_status == Signature.STATUS_APPROVED
        assert signature.verified_at is not None
        assert petition.signature_count == initial_count + 1
    
    def test_approve_already_approved(self):
        """Test approving an already approved signature does nothing"""
        signature = SignatureFactory(
            verification_status=Signature.STATUS_APPROVED
        )
        petition = signature.petition
        initial_count = petition.signature_count
        
        signature.approve()
        petition.refresh_from_db()
        
        # Count should not increase again
        assert petition.signature_count == initial_count
    
    def test_reject_signature(self):
        """Test signature rejection method"""
        signature = SignatureFactory(
            verification_status=Signature.STATUS_PENDING
        )
        
        signature.reject("Invalid certificate")
        signature.refresh_from_db()
        
        assert signature.verification_status == Signature.STATUS_REJECTED
        assert signature.verification_notes == "Invalid certificate"
    
    def test_unique_cpf_per_petition(self):
        """Test unique constraint on CPF per petition"""
        petition = PetitionFactory()
        cpf_hash = Signature.hash_cpf("12345678901")
        
        # First signature
        SignatureFactory(
            petition=petition,
            cpf_hash=cpf_hash
        )
        
        # Second signature with same CPF should fail
        with pytest.raises(Exception):
            SignatureFactory(
            petition=petition,
                cpf_hash=cpf_hash
            )
    
    def test_same_cpf_different_petitions(self):
        """Test same CPF can sign different petitions"""
        petition1 = PetitionFactory()
        petition2 = PetitionFactory()
        cpf_hash = Signature.hash_cpf("12345678901")
        
        sig1 = SignatureFactory(petition=petition1, cpf_hash=cpf_hash)
        sig2 = SignatureFactory(petition=petition2, cpf_hash=cpf_hash)
        
        assert sig1.pk is not None
        assert sig2.pk is not None
