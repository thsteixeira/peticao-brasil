"""
Unit tests for Petition model
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from apps.petitions.models import Petition
from tests.factories import PetitionFactory, UserFactory, CategoryFactory


@pytest.mark.unit
@pytest.mark.django_db
class TestPetitionModel:
    """Test Petition model methods and properties"""
    
    def test_petition_creation(self):
        """Test petition can be created"""
        petition = PetitionFactory()
        assert petition.pk is not None
        assert petition.title
        assert petition.uuid is not None
        assert petition.slug
    
    def test_petition_str(self):
        """Test petition string representation"""
        petition = PetitionFactory(title="Test Petition")
        assert str(petition) == "Test Petition"
    
    def test_petition_get_absolute_url(self):
        """Test petition URL generation"""
        petition = PetitionFactory()
        url = petition.get_absolute_url()
        assert f'/petitions/{petition.uuid}/' in url
    
    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        petition = PetitionFactory(signature_goal=1000, signature_count=250)
        assert petition.progress_percentage == 25
    
    def test_progress_percentage_over_100(self):
        """Test progress percentage caps at 100%"""
        petition = PetitionFactory(signature_goal=100, signature_count=150)
        assert petition.progress_percentage == 100
    
    def test_days_remaining_with_deadline(self):
        """Test days remaining calculation"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        petition = PetitionFactory(deadline=tomorrow)
        assert petition.days_remaining == 1
    
    def test_days_remaining_no_deadline(self):
        """Test days remaining with no deadline"""
        petition = PetitionFactory(deadline=None)
        assert petition.days_remaining is None
    
    def test_is_expired_true(self):
        """Test is_expired when deadline passed"""
        yesterday = timezone.now().date() - timedelta(days=1)
        petition = PetitionFactory(deadline=yesterday)
        assert petition.is_expired is True
    
    def test_is_expired_false(self):
        """Test is_expired when deadline not passed"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        petition = PetitionFactory(deadline=tomorrow)
        assert petition.is_expired is False
    
    def test_is_successful_true(self):
        """Test is_successful when goal reached"""
        petition = PetitionFactory(signature_goal=100, signature_count=150)
        assert petition.is_successful is True
    
    def test_is_successful_false(self):
        """Test is_successful when goal not reached"""
        petition = PetitionFactory(signature_goal=1000, signature_count=50)
        assert petition.is_successful is False
    
    def test_increment_signature_count(self):
        """Test signature count increment"""
        petition = PetitionFactory(signature_count=0)
        initial_count = petition.signature_count
        
        petition.increment_signature_count()
        petition.refresh_from_db()
        
        assert petition.signature_count == initial_count + 1
    
    def test_increment_view_count(self):
        """Test view count increment"""
        petition = PetitionFactory(view_count=0)
        initial_count = petition.view_count
        
        petition.increment_view_count()
        petition.refresh_from_db()
        
        assert petition.view_count == initial_count + 1
    
    def test_auto_status_change_to_expired(self):
        """Test petition auto-expires when deadline passes"""
        yesterday = timezone.now().date() - timedelta(days=1)
        petition = PetitionFactory(
            status=Petition.STATUS_ACTIVE,
            deadline=yesterday
        )
        
        petition.save()
        petition.refresh_from_db()
        
        assert petition.status == Petition.STATUS_EXPIRED
        assert petition.is_active is False
    
    def test_auto_status_change_to_completed(self):
        """Test petition auto-completes when goal reached"""
        petition = PetitionFactory(
            status=Petition.STATUS_ACTIVE,
            signature_goal=100,
            signature_count=0
        )
        
        # Manually set count to reach goal
        petition.signature_count = 100
        petition.save()
        petition.refresh_from_db()
        
        assert petition.status == Petition.STATUS_COMPLETED
    
    def test_slug_generation(self):
        """Test slug is auto-generated from title"""
        petition = PetitionFactory(title="Test Petition Title")
        assert petition.slug == "test-petition-title"
    
    def test_unique_cpf_per_petition_via_hash(self):
        """Test CPF hash ensures uniqueness"""
        from apps.signatures.models import Signature
        
        petition = PetitionFactory()
        cpf = "12345678901"
        cpf_hash = Signature.hash_cpf(cpf)
        
        # First signature should succeed
        sig1 = Signature.objects.create(
            petition=petition,
            full_name="User 1",
            cpf_hash=cpf_hash,
            email="user1@example.com",
            city="São Paulo",
            state="SP"
        )
        assert sig1.pk is not None
        
        # Second signature with same CPF should fail
        with pytest.raises(Exception):  # UniqueConstraint violation
            Signature.objects.create(
                petition=petition,
                full_name="User 2",
                cpf_hash=cpf_hash,
                email="user2@example.com",
                city="Rio de Janeiro",
                state="RJ"
            )
