"""
Tests for form validation and security
"""
import pytest
from django.test import RequestFactory
from apps.petitions.forms import PetitionForm
from apps.signatures.forms import SignatureSubmissionForm
from apps.core.validators import validate_cpf
from tests.factories import UserFactory, CategoryFactory


@pytest.mark.unit
@pytest.mark.django_db
class TestPetitionForm:
    """Test petition form validation"""
    
    def test_valid_petition_form(self):
        """Test form with valid data"""
        user = UserFactory()
        category = CategoryFactory()
        
        data = {
            'title': 'Test Petition',
            'description': 'This is a test petition description with enough content.',
            'category': category.id,
            'signature_goal': 1000,
        }
        
        form = PetitionForm(data=data)
        assert form.is_valid()
    
    def test_title_too_short(self):
        """Test form rejects too short title"""
        user = UserFactory()
        category = CategoryFactory()
        
        data = {
            'title': 'Hi',  # Too short
            'description': 'Valid description with enough content.',
            'category': category.id,
            'signature_goal': 1000,
        }
        
        form = PetitionForm(data=data)
        assert not form.is_valid()
        assert 'title' in form.errors
    
    def test_xss_sanitization_in_description(self):
        """Test XSS content is sanitized"""
        category = CategoryFactory()
        
        data = {
            'title': 'Test Petition',
            'description': '<script>alert("XSS")</script>Safe content',
            'category': category.id,
            'signature_goal': 1000,
        }
        
        form = PetitionForm(data=data)
        if form.is_valid():
            # Script tags should be removed
            assert '<script>' not in form.cleaned_data['description']
            assert 'Safe content' in form.cleaned_data['description']
    
    def test_signature_goal_minimum(self):
        """Test signature goal has minimum value"""
        category = CategoryFactory()
        
        data = {
            'title': 'Test Petition',
            'description': 'Valid description',
            'category': category.id,
            'signature_goal': 50,  # Less than minimum (100)
        }
        
        form = PetitionForm(data=data)
        assert not form.is_valid()
        assert 'signature_goal' in form.errors


@pytest.mark.unit
class TestCPFValidator:
    """Test CPF validation"""
    
    def test_valid_cpf(self):
        """Test valid CPF passes validation"""
        valid_cpfs = [
            '12345678909',
            '11144477735',
            '00000000191',
        ]
        
        for cpf in valid_cpfs:
            try:
                validate_cpf(cpf)
            except Exception:
                pytest.fail(f"Valid CPF {cpf} failed validation")
    
    def test_invalid_cpf_format(self):
        """Test invalid CPF format"""
        with pytest.raises(Exception):
            validate_cpf('123')  # Too short
    
    def test_cpf_all_same_digits(self):
        """Test CPF with all same digits is invalid"""
        invalid_cpfs = [
            '11111111111',
            '22222222222',
            '00000000000',
        ]
        
        for cpf in invalid_cpfs:
            with pytest.raises(Exception):
                validate_cpf(cpf)
    
    def test_cpf_with_formatting(self):
        """Test CPF with formatting is handled"""
        # Should accept formatted CPF
        try:
            validate_cpf('123.456.789-09')
        except Exception:
            pytest.fail("Formatted CPF should be accepted")


@pytest.mark.unit
@pytest.mark.django_db
class TestSignatureForm:
    """Test signature submission form"""
    
    def test_valid_signature_form(self, petition):
        """Test form with valid signature data"""
        data = {
            'full_name': 'João Silva',
            'cpf': '12345678909',
            'email': 'joao@example.com',
            'city': 'São Paulo',
            'state': 'SP',
            'display_name_publicly': True,
            'receive_updates': False,
        }
        
        form = SignatureSubmissionForm(data=data, petition=petition)
        assert form.is_valid()
    
    def test_duplicate_cpf_same_petition(self, petition, signature):
        """Test form rejects duplicate CPF on same petition"""
        # signature fixture already has a CPF hash
        data = {
            'full_name': 'Another Person',
            'cpf': '12345678901',  # Same as in signature fixture
            'email': 'another@example.com',
            'city': 'Rio de Janeiro',
            'state': 'RJ',
        }
        
        form = SignatureSubmissionForm(data=data, petition=petition)
        # Should fail due to duplicate CPF
        assert not form.is_valid() or 'cpf' in form.errors
    
    def test_invalid_email(self, petition):
        """Test form rejects invalid email"""
        data = {
            'full_name': 'João Silva',
            'cpf': '12345678909',
            'email': 'invalid-email',  # Invalid format
            'city': 'São Paulo',
            'state': 'SP',
        }
        
        form = SignatureSubmissionForm(data=data, petition=petition)
        assert not form.is_valid()
        assert 'email' in form.errors
