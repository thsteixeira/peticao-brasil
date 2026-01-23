# Petição Brasil - Integration Testing

**Project Phase:** Planning - Phase 7  
**Document Version:** 1.1  
**Last Updated:** January 22, 2026  
**Status:** Draft  
**Domain:** peticaobrasil.com.br

---

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Test Environment Setup](#test-environment-setup)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [End-to-End Tests](#end-to-end)
6. [Performance Tests](#performance-tests)
7. [Security Tests](#security-tests)
8. [Test Data and Fixtures](#test-data-and-fixtures)
9. [Continuous Integration](#continuous-integration)
10. [Test Coverage Goals](#test-coverage-goals)

---

## Testing Strategy

### Testing Pyramid

```
                    ▲
                   / \
                  /   \
                 /  E2E \         ~10% - Browser automation
                /-------\
               /         \
              / Integration\      ~30% - Service layer
             /-------------\
            /               \
           /    Unit Tests   \   ~60% - Functions, models
          /___________________\
```

### Test Levels

1. **Unit Tests (60%)**
   - Models (validation, methods)
   - Validators
   - Utils and helpers
   - Service classes

2. **Integration Tests (30%)**
   - Views with database
   - File uploads with S3
   - PDF generation pipeline
   - Verification pipeline
   - Email sending

3. **End-to-End Tests (10%)**
   - Complete user journeys
   - Browser automation
   - Cross-browser compatibility

### Testing Principles

- **Fast**: Unit tests < 1s, Integration < 10s
- **Isolated**: No external dependencies in unit tests
- **Repeatable**: Same input = same output
- **Comprehensive**: Cover happy paths + edge cases
- **Maintainable**: Clear, readable test code

---

## Test Environment Setup

### Dependencies

```python
# requirements-test.txt

# Testing frameworks
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
pytest-xdist==3.5.0  # Parallel test execution

# Mocking and fixtures
factory-boy==3.3.0
faker==20.1.0
freezegun==1.4.0  # Time mocking

# HTTP testing
responses==0.24.1  # Mock HTTP requests

# Browser automation
selenium==4.16.0
playwright==1.40.0

# Performance testing
locust==2.20.0

# Security testing
bandit==1.7.5
safety==2.3.5
```

### pytest Configuration

```ini
# pytest.ini

[pytest]
DJANGO_SETTINGS_MODULE = pressiona.settings_test
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --cov=pressionaapp
    --cov-report=html
    --cov-report=term-missing
    --no-migrations
    --reuse-db
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests (>1s)
    security: Security tests
    e2e: End-to-end tests
```

### Test Settings

```python
# pressiona/settings_test.py

from .settings import *

# Use in-memory SQLite for speed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for speed
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use local file storage instead of S3
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = '/tmp/pressiona_test_media'

# Disable password hashing for speed
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Celery - execute synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable throttling
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/hour',
    'user': '10000/hour',
}

# Mock Turnstile
TURNSTILE_SECRET_KEY = 'test_secret_key'
TURNSTILE_SITE_KEY = 'test_site_key'
```

---

## Unit Tests

### Model Tests

```python
# pressionaapp/tests/test_models.py

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from pressionaapp.models import Category, Petition, Signature
from pressionaapp.tests.factories import (
    UserFactory, CategoryFactory, PetitionFactory, SignatureFactory
)

User = get_user_model()


@pytest.mark.django_db
class TestCategoryModel:
    """Test Category model."""
    
    def test_create_category(self):
        """Test creating a category."""
        category = CategoryFactory(name="Saúde", slug="saude")
        assert category.name == "Saúde"
        assert category.slug == "saude"
        assert category.is_active is True
    
    def test_category_str(self):
        """Test category string representation."""
        category = CategoryFactory(name="Educação")
        assert str(category) == "Educação"
    
    def test_duplicate_slug(self):
        """Test that duplicate slugs are not allowed."""
        CategoryFactory(slug="saude")
        with pytest.raises(ValidationError):
            category = Category(name="Saúde 2", slug="saude")
            category.full_clean()


@pytest.mark.django_db
class TestPetitionModel:
    """Test Petition model."""
    
    def test_create_petition(self):
        """Test creating a petition."""
        user = UserFactory()
        category = CategoryFactory()
        petition = PetitionFactory(
            title="Test Petition",
            creator=user,
            category=category,
            signature_goal=1000
        )
        assert petition.title == "Test Petition"
        assert petition.signature_count == 0
        assert petition.status == "draft"
    
    def test_petition_uuid_generated(self):
        """Test that UUID is auto-generated."""
        petition = PetitionFactory()
        assert petition.uuid is not None
        assert len(str(petition.uuid)) == 36
    
    def test_petition_slug_generated(self):
        """Test that slug is auto-generated from title."""
        petition = PetitionFactory(title="Melhoria da Saúde Pública")
        assert petition.slug == "melhoria-da-saude-publica"
    
    def test_petition_progress_percentage(self):
        """Test progress percentage calculation."""
        petition = PetitionFactory(signature_goal=1000)
        petition.signature_count = 250
        assert petition.progress_percentage == 25
    
    def test_petition_is_active(self):
        """Test is_active property."""
        petition = PetitionFactory(status="active")
        assert petition.is_active is True
        
        petition.status = "closed"
        assert petition.is_active is False
    
    def test_petition_is_expired(self):
        """Test is_expired property."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Not expired
        petition = PetitionFactory(
            deadline=timezone.now() + timedelta(days=10)
        )
        assert petition.is_expired is False
        
        # Expired
        petition.deadline = timezone.now() - timedelta(days=1)
        assert petition.is_expired is True
        
        # No deadline
        petition.deadline = None
        assert petition.is_expired is False
    
    def test_petition_days_remaining(self):
        """Test days_remaining property."""
        from django.utils import timezone
        from datetime import timedelta
        
        petition = PetitionFactory(
            deadline=timezone.now() + timedelta(days=15, hours=12)
        )
        assert petition.days_remaining == 15
    
    def test_petition_publish(self):
        """Test publishing a petition."""
        petition = PetitionFactory(status="draft")
        petition.publish()
        assert petition.status == "active"
        assert petition.published_at is not None
    
    def test_petition_close(self):
        """Test closing a petition."""
        petition = PetitionFactory(status="active")
        petition.close()
        assert petition.status == "closed"


@pytest.mark.django_db
class TestSignatureModel:
    """Test Signature model."""
    
    def test_create_signature(self):
        """Test creating a signature."""
        petition = PetitionFactory()
        signature = SignatureFactory(
            petition=petition,
            name="João Silva",
            cpf_hash="abc123",
            email="joao@example.com"
        )
        assert signature.name == "João Silva"
        assert signature.verification_status == "pending"
    
    def test_signature_unique_cpf_per_petition(self):
        """Test that CPF hash must be unique per petition."""
        petition = PetitionFactory()
        SignatureFactory(petition=petition, cpf_hash="hash1")
        
        with pytest.raises(ValidationError):
            signature = Signature(
                petition=petition,
                cpf_hash="hash1",
                name="Outro Nome",
                email="outro@example.com"
            )
            signature.full_clean()
    
    def test_signature_display_name_full(self):
        """Test display_name with full name visible."""
        signature = SignatureFactory(
            name="João Silva Santos",
            show_full_name=True
        )
        assert signature.display_name == "João Silva Santos"
    
    def test_signature_display_name_initials(self):
        """Test display_name with initials only."""
        signature = SignatureFactory(
            name="João Silva Santos",
            show_full_name=False
        )
        assert signature.display_name == "João S."
    
    def test_signature_approve(self):
        """Test approving a signature."""
        signature = SignatureFactory(verification_status="pending")
        petition = signature.petition
        initial_count = petition.signature_count
        
        signature.approve()
        
        assert signature.verification_status == "approved"
        assert signature.verified_at is not None
        
        # Check signature count incremented
        petition.refresh_from_db()
        assert petition.signature_count == initial_count + 1
    
    def test_signature_reject(self):
        """Test rejecting a signature."""
        signature = SignatureFactory(verification_status="pending")
        
        signature.reject("Invalid certificate")
        
        assert signature.verification_status == "rejected"
        assert signature.rejection_reason == "Invalid certificate"
```

### Validator Tests

```python
# pressionaapp/tests/test_validators.py

import pytest
from django.core.exceptions import ValidationError
from pressionaapp.validators import (
    validate_cpf,
    validate_brazilian_name,
    validate_petition_title,
    validate_petition_description,
    validate_signature_goal,
)


class TestCPFValidator:
    """Test CPF validation."""
    
    def test_valid_cpf_no_formatting(self):
        """Test valid CPF without formatting."""
        cpf = validate_cpf("12345678909")
        assert cpf == "12345678909"
    
    def test_valid_cpf_with_formatting(self):
        """Test valid CPF with formatting."""
        cpf = validate_cpf("123.456.789-09")
        assert cpf == "12345678909"
    
    def test_invalid_cpf(self):
        """Test invalid CPF."""
        with pytest.raises(ValidationError):
            validate_cpf("12345678900")
    
    def test_cpf_all_same_digits(self):
        """Test CPF with all same digits (invalid)."""
        with pytest.raises(ValidationError):
            validate_cpf("111.111.111-11")


class TestNameValidator:
    """Test name validation."""
    
    def test_valid_full_name(self):
        """Test valid full name."""
        name = validate_brazilian_name("João Silva")
        assert name == "João Silva"
    
    def test_valid_name_with_accents(self):
        """Test name with accents."""
        name = validate_brazilian_name("José María Souza")
        assert name == "José María Souza"
    
    def test_name_with_extra_whitespace(self):
        """Test name with extra whitespace."""
        name = validate_brazilian_name("  João   Silva  ")
        assert name == "João Silva"
    
    def test_single_name_invalid(self):
        """Test single name (invalid)."""
        with pytest.raises(ValidationError):
            validate_brazilian_name("João")
    
    def test_name_too_short(self):
        """Test name too short."""
        with pytest.raises(ValidationError):
            validate_brazilian_name("Jo")
    
    def test_name_with_numbers(self):
        """Test name with numbers (invalid)."""
        with pytest.raises(ValidationError):
            validate_brazilian_name("João Silva 123")


class TestPetitionTitleValidator:
    """Test petition title validation."""
    
    def test_valid_title(self):
        """Test valid petition title."""
        title = validate_petition_title("Melhoria da Saúde Pública")
        assert title == "Melhoria da Saúde Pública"
    
    def test_title_too_short(self):
        """Test title too short."""
        with pytest.raises(ValidationError):
            validate_petition_title("Curto")
    
    def test_title_too_long(self):
        """Test title too long."""
        with pytest.raises(ValidationError):
            validate_petition_title("A" * 201)
    
    def test_title_with_html(self):
        """Test title with HTML (invalid)."""
        with pytest.raises(ValidationError):
            validate_petition_title("Petition <script>alert('xss')</script>")
    
    def test_title_excessive_punctuation(self):
        """Test title with excessive punctuation."""
        with pytest.raises(ValidationError):
            validate_petition_title("Melhoria urgente!!!!!!")


class TestPetitionDescriptionValidator:
    """Test petition description validation."""
    
    def test_valid_description(self):
        """Test valid description."""
        desc = "A" * 150
        result = validate_petition_description(desc)
        assert len(result) == 150
    
    def test_description_too_short(self):
        """Test description too short."""
        with pytest.raises(ValidationError):
            validate_petition_description("Muito curto")
    
    def test_description_with_urls(self):
        """Test description with URLs (allowed up to 5)."""
        desc = "A" * 100 + " https://example.com"
        result = validate_petition_description(desc)
        assert "https://example.com" in result
    
    def test_description_too_many_urls(self):
        """Test description with too many URLs."""
        urls = " ".join([f"https://example{i}.com" for i in range(6)])
        desc = "A" * 100 + " " + urls
        with pytest.raises(ValidationError):
            validate_petition_description(desc)


class TestSignatureGoalValidator:
    """Test signature goal validation."""
    
    def test_valid_goal(self):
        """Test valid signature goal."""
        assert validate_signature_goal(1000) == 1000
    
    def test_goal_too_low(self):
        """Test goal too low."""
        with pytest.raises(ValidationError):
            validate_signature_goal(5)
    
    def test_goal_too_high(self):
        """Test goal too high."""
        with pytest.raises(ValidationError):
            validate_signature_goal(2000000)
```

### Service Tests

```python
# pressionaapp/tests/test_pdf_generator.py

import pytest
from io import BytesIO
from pressionaapp.services.pdf_generator import PetitionPDFGenerator
from pressionaapp.tests.factories import PetitionFactory


@pytest.mark.django_db
class TestPetitionPDFGenerator:
    """Test PDF generation service."""
    
    def test_generate_pdf(self):
        """Test generating a PDF."""
        petition = PetitionFactory(
            title="Test Petition",
            description="Test description for petition."
        )
        
        generator = PetitionPDFGenerator(petition)
        pdf_buffer = generator.generate()
        
        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.tell() > 0  # Has content
    
    def test_pdf_has_correct_header(self):
        """Test PDF has correct header."""
        petition = PetitionFactory()
        generator = PetitionPDFGenerator(petition)
        pdf_buffer = generator.generate()
        
        pdf_buffer.seek(0)
        header = pdf_buffer.read(5)
        assert header == b'%PDF-'
    
    def test_calculate_content_hash(self):
        """Test content hash calculation."""
        petition = PetitionFactory(
            title="Test",
            description="Description"
        )
        
        generator = PetitionPDFGenerator(petition)
        hash1 = generator.calculate_content_hash()
        hash2 = generator.calculate_content_hash()
        
        # Same content = same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex
    
    def test_embed_uuid(self):
        """Test UUID embedding."""
        petition = PetitionFactory()
        generator = PetitionPDFGenerator(petition)
        pdf_buffer = generator.generate()
        
        # Extract and verify UUID
        # (Detailed implementation would use PyPDF2)
        assert pdf_buffer is not None
```

---

## Integration Tests

### View Tests

```python
# pressionaapp/tests/test_views.py

import pytest
from django.urls import reverse
from django.test import Client
from pressionaapp.tests.factories import (
    UserFactory, PetitionFactory, CategoryFactory
)


@pytest.mark.django_db
class TestPetitionListView:
    """Test petition list view."""
    
    def test_list_view_accessible(self):
        """Test that list view is accessible."""
        client = Client()
        url = reverse('pressionaapp:petition_list')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'petitions' in response.context
    
    def test_list_view_shows_active_petitions(self):
        """Test that only active petitions are shown."""
        PetitionFactory(status='active', title="Active 1")
        PetitionFactory(status='active', title="Active 2")
        PetitionFactory(status='draft', title="Draft")
        
        client = Client()
        url = reverse('pressionaapp:petition_list')
        response = client.get(url)
        
        petitions = response.context['petitions']
        assert len(petitions) == 2
    
    def test_list_view_filter_by_category(self):
        """Test filtering by category."""
        category = CategoryFactory(slug='saude')
        PetitionFactory(status='active', category=category)
        PetitionFactory(status='active')  # Different category
        
        client = Client()
        url = reverse('pressionaapp:petition_list')
        response = client.get(url, {'category': 'saude'})
        
        petitions = response.context['petitions']
        assert len(petitions) == 1
    
    def test_list_view_search(self):
        """Test search functionality."""
        PetitionFactory(status='active', title="Melhoria da Saúde")
        PetitionFactory(status='active', title="Educação Pública")
        
        client = Client()
        url = reverse('pressionaapp:petition_list')
        response = client.get(url, {'q': 'saúde'})
        
        petitions = response.context['petitions']
        assert len(petitions) == 1
        assert "Saúde" in petitions[0].title


@pytest.mark.django_db
class TestPetitionDetailView:
    """Test petition detail view."""
    
    def test_detail_view_accessible(self):
        """Test that detail view is accessible."""
        petition = PetitionFactory(status='active')
        
        client = Client()
        url = reverse('pressionaapp:petition_detail', args=[petition.id, petition.slug])
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['petition'] == petition
    
    def test_detail_view_404_for_nonexistent(self):
        """Test 404 for non-existent petition."""
        client = Client()
        url = reverse('pressionaapp:petition_detail', args=[99999, 'fake-slug'])
        response = client.get(url)
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestPetitionCreateView:
    """Test petition creation view."""
    
    def test_create_view_requires_login(self):
        """Test that create view requires authentication."""
        client = Client()
        url = reverse('pressionaapp:petition_create')
        response = client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_create_view_accessible_when_logged_in(self):
        """Test that logged-in users can access create view."""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        
        url = reverse('pressionaapp:petition_create')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_create_petition_with_valid_data(self):
        """Test creating a petition with valid data."""
        user = UserFactory()
        category = CategoryFactory()
        
        client = Client()
        client.force_login(user)
        
        url = reverse('pressionaapp:petition_create')
        data = {
            'title': 'Melhoria da Saúde Pública',
            'description': 'A' * 150,
            'category': category.id,
            'signature_goal': 1000,
        }
        
        response = client.post(url, data)
        
        assert response.status_code == 302  # Redirect on success
        assert Petition.objects.filter(title='Melhoria da Saúde Pública').exists()
    
    def test_create_petition_with_invalid_data(self):
        """Test creating a petition with invalid data."""
        user = UserFactory()
        
        client = Client()
        client.force_login(user)
        
        url = reverse('pressionaapp:petition_create')
        data = {
            'title': 'Short',  # Too short
            'description': 'Also short',  # Too short
            'signature_goal': 5,  # Too low
        }
        
        response = client.post(url, data)
        
        assert response.status_code == 200  # Stay on form
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
@pytest.mark.integration
class TestSignatureUploadView:
    """Test signature upload view."""
    
    def test_upload_view_accessible(self):
        """Test that upload view is accessible."""
        petition = PetitionFactory(status='active')
        
        client = Client()
        url = reverse('pressionaapp:signature_upload', args=[petition.id])
        response = client.get(url)
        
        assert response.status_code == 200
    
    @pytest.mark.slow
    def test_upload_signed_pdf(self, tmp_path):
        """Test uploading a signed PDF."""
        petition = PetitionFactory(status='active')
        
        # Create a fake PDF file
        pdf_content = b'%PDF-1.4\n%fake pdf content'
        pdf_file = tmp_path / "signed.pdf"
        pdf_file.write_bytes(pdf_content)
        
        client = Client()
        url = reverse('pressionaapp:signature_upload', args=[petition.id])
        
        with open(pdf_file, 'rb') as f:
            data = {
                'pdf_file': f,
                'name': 'João Silva Santos',
                'cpf': '123.456.789-09',
                'email': 'joao@example.com',
                'city': 'São Paulo',
                'state': 'SP',
            }
            response = client.post(url, data)
        
        # Should redirect to verification status page
        assert response.status_code == 302
```

### File Upload Tests

```python
# pressionaapp/tests/test_file_upload.py

import pytest
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from pressionaapp.validators import SignedPDFValidator
from pressionaapp.utils.file_handlers import SecureFileHandler


class TestSignedPDFValidator:
    """Test PDF file validator."""
    
    def test_valid_pdf(self):
        """Test validating a valid PDF."""
        pdf_content = b'%PDF-1.4\n' + b'x' * 1000
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        validator = SignedPDFValidator()
        # Should not raise
        validator(pdf_file)
    
    def test_file_too_large(self):
        """Test file size validation."""
        from django.core.exceptions import ValidationError
        
        # 11MB file (exceeds 10MB limit)
        pdf_content = b'%PDF-1.4\n' + b'x' * (11 * 1024 * 1024)
        pdf_file = SimpleUploadedFile("large.pdf", pdf_content)
        
        validator = SignedPDFValidator()
        with pytest.raises(ValidationError, match="muito grande"):
            validator(pdf_file)
    
    def test_invalid_extension(self):
        """Test file extension validation."""
        from django.core.exceptions import ValidationError
        
        file = SimpleUploadedFile("test.txt", b"content")
        
        validator = SignedPDFValidator()
        with pytest.raises(ValidationError, match="Tipo de arquivo inválido"):
            validator(file)
    
    def test_empty_file(self):
        """Test empty file validation."""
        from django.core.exceptions import ValidationError
        
        pdf_file = SimpleUploadedFile("empty.pdf", b"")
        
        validator = SignedPDFValidator()
        with pytest.raises(ValidationError, match="vazio"):
            validator(pdf_file)


class TestSecureFileHandler:
    """Test secure file handling."""
    
    def test_generate_secure_filename(self):
        """Test secure filename generation."""
        filename = SecureFileHandler.generate_secure_filename("test.pdf")
        
        # Should contain signatures/, year, month, uuid
        assert filename.startswith("signatures/")
        assert filename.endswith(".pdf")
        assert len(filename.split('/')) == 4  # signatures/year/month/file
    
    def test_filename_path_traversal_prevention(self):
        """Test that path traversal is prevented."""
        malicious = "../../../etc/passwd.pdf"
        filename = SecureFileHandler.generate_secure_filename(malicious)
        
        # Should not contain ../
        assert "../" not in filename
        assert filename.endswith(".pdf")
```

### Verification Pipeline Tests

```python
# pressionaapp/tests/test_signature_verification.py

import pytest
from unittest.mock import Mock, patch
from pressionaapp.services.signature_verifier import SignatureVerifier
from pressionaapp.tests.factories import PetitionFactory, SignatureFactory


@pytest.mark.django_db
@pytest.mark.integration
class TestSignatureVerifier:
    """Test signature verification service."""
    
    @patch('pressionaapp.services.signature_verifier.PDFValidator')
    @patch('pressionaapp.services.signature_verifier.DigitalSignatureValidator')
    def test_verify_valid_signature(self, mock_sig_validator, mock_pdf_validator):
        """Test verifying a valid signature."""
        petition = PetitionFactory()
        signature = SignatureFactory(
            petition=petition,
            verification_status='pending'
        )
        
        # Mock PDF validator
        mock_pdf_validator.return_value.extract_text.return_value = "petition text"
        mock_pdf_validator.return_value.extract_uuid.return_value = str(petition.uuid)
        
        # Mock signature validator
        mock_sig_validator.return_value.validate.return_value = {
            'is_valid': True,
            'level': 'advanced',
            'signer_name': 'João Silva',
            'cpf': '12345678909',
        }
        
        verifier = SignatureVerifier(signature, "fake_pdf_path")
        result = verifier.verify()
        
        assert result.status == 'approved'
        assert result.is_success is True
    
    @patch('pressionaapp.services.signature_verifier.PDFValidator')
    def test_verify_content_hash_mismatch(self, mock_pdf_validator):
        """Test verification fails with content hash mismatch."""
        petition = PetitionFactory(content_hash="original_hash")
        signature = SignatureFactory(
            petition=petition,
            verification_status='pending'
        )
        
        # Mock different content
        mock_pdf_validator.return_value.extract_text.return_value = "different text"
        
        verifier = SignatureVerifier(signature, "fake_pdf_path")
        result = verifier.verify()
        
        assert result.status == 'rejected'
        assert 'conteúdo' in result.message.lower()
    
    @patch('pressionaapp.services.signature_verifier.PDFValidator')
    def test_verify_uuid_mismatch(self, mock_pdf_validator):
        """Test verification fails with UUID mismatch."""
        petition = PetitionFactory()
        signature = SignatureFactory(
            petition=petition,
            verification_status='pending'
        )
        
        # Mock matching content but different UUID
        mock_pdf_validator.return_value.extract_text.return_value = petition.description
        mock_pdf_validator.return_value.extract_uuid.return_value = "wrong-uuid"
        
        verifier = SignatureVerifier(signature, "fake_pdf_path")
        result = verifier.verify()
        
        assert result.status == 'rejected'
        assert 'uuid' in result.message.lower()
    
    @patch('pressionaapp.services.signature_verifier.PDFValidator')
    @patch('pressionaapp.services.signature_verifier.DigitalSignatureValidator')
    def test_verify_cpf_mismatch(self, mock_sig_validator, mock_pdf_validator):
        """Test verification fails with CPF mismatch."""
        petition = PetitionFactory()
        signature = SignatureFactory(
            petition=petition,
            cpf_hash="hash_of_12345678909"
        )
        
        # Mock PDF and UUID correct
        mock_pdf_validator.return_value.extract_text.return_value = petition.description
        mock_pdf_validator.return_value.extract_uuid.return_value = str(petition.uuid)
        
        # Mock different CPF in certificate
        mock_sig_validator.return_value.validate.return_value = {
            'is_valid': True,
            'level': 'advanced',
            'signer_name': 'João Silva',
            'cpf': '98765432100',  # Different CPF
        }
        
        verifier = SignatureVerifier(signature, "fake_pdf_path")
        result = verifier.verify()
        
        assert result.status == 'rejected'
        assert 'cpf' in result.message.lower()
```

---

## End-to-End Tests

### Selenium Tests

```python
# pressionaapp/tests/test_e2e.py

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from pressionaapp.tests.factories import UserFactory, CategoryFactory


@pytest.mark.e2e
class TestPetitionCreationJourney(StaticLiveServerTestCase):
    """End-to-end test for petition creation."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()
    
    def test_complete_petition_creation_flow(self):
        """Test complete petition creation flow."""
        # Setup
        user = UserFactory(username='testuser', password='testpass123')
        category = CategoryFactory(name='Saúde')
        
        driver = self.driver
        
        # 1. Navigate to homepage
        driver.get(f'{self.live_server_url}/')
        assert 'Pressiona' in driver.title
        
        # 2. Click login
        login_link = driver.find_element(By.LINK_TEXT, 'Entrar')
        login_link.click()
        
        # 3. Login
        username_input = driver.find_element(By.NAME, 'username')
        password_input = driver.find_element(By.NAME, 'password')
        username_input.send_keys('testuser')
        password_input.send_keys('testpass123')
        
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # 4. Navigate to create petition
        create_button = driver.find_element(By.LINK_TEXT, 'Criar Petição')
        create_button.click()
        
        # 5. Fill petition form
        title_input = driver.find_element(By.NAME, 'title')
        title_input.send_keys('Melhoria do Atendimento Hospitalar')
        
        description_textarea = driver.find_element(By.NAME, 'description')
        description_textarea.send_keys('A' * 150)
        
        category_select = driver.find_element(By.NAME, 'category')
        category_select.send_keys('Saúde')
        
        goal_input = driver.find_element(By.NAME, 'signature_goal')
        goal_input.clear()
        goal_input.send_keys('1000')
        
        # 6. Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # 7. Verify redirect to petition detail
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'petition-title'))
        )
        
        petition_title = driver.find_element(By.CLASS_NAME, 'petition-title')
        assert 'Melhoria do Atendimento Hospitalar' in petition_title.text


@pytest.mark.e2e
class TestPetitionSigningJourney(StaticLiveServerTestCase):
    """End-to-end test for petition signing."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()
    
    def test_download_pdf_flow(self):
        """Test downloading petition PDF."""
        from pressionaapp.tests.factories import PetitionFactory
        
        petition = PetitionFactory(status='active')
        
        driver = self.driver
        
        # 1. Navigate to petition detail
        driver.get(f'{self.live_server_url}/peticoes/{petition.id}/{petition.slug}/')
        
        # 2. Click "Assinar Esta Petição"
        sign_button = driver.find_element(By.LINK_TEXT, 'Assinar Esta Petição')
        sign_button.click()
        
        # 3. Click "Baixar PDF"
        download_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Baixar PDF para Assinar'))
        )
        download_button.click()
        
        # Note: Actual file download testing requires additional setup
        # For now, just verify the button is clickable
```

---

## Performance Tests

### Load Testing with Locust

```python
# pressionaapp/tests/locustfile.py

from locust import HttpUser, task, between
import random


class PetitionUser(HttpUser):
    """Simulated user for load testing."""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Called when a user starts."""
        pass
    
    @task(3)
    def view_petition_list(self):
        """View petition list (most common action)."""
        self.client.get("/peticoes/")
    
    @task(2)
    def view_petition_detail(self):
        """View petition detail."""
        # Assuming petition IDs 1-100 exist
        petition_id = random.randint(1, 100)
        self.client.get(f"/peticoes/{petition_id}/")
    
    @task(1)
    def search_petitions(self):
        """Search petitions."""
        queries = ['saúde', 'educação', 'meio ambiente']
        query = random.choice(queries)
        self.client.get(f"/peticoes/?q={query}")
    
    @task(1)
    def filter_by_category(self):
        """Filter petitions by category."""
        categories = ['saude', 'educacao', 'meio-ambiente']
        category = random.choice(categories)
        self.client.get(f"/peticoes/?category={category}")


# Run with:
# locust -f pressionaapp/tests/locustfile.py --host=http://localhost:8000
```

---

## Security Tests

### Security Scan with Bandit

```bash
# Run Bandit security scanner
bandit -r pressionaapp/ -ll

# Check dependencies for vulnerabilities
safety check
```

### XSS Tests

```python
# pressionaapp/tests/test_security.py

import pytest
from django.test import Client
from pressionaapp.tests.factories import PetitionFactory


@pytest.mark.django_db
@pytest.mark.security
class TestXSSPrevention:
    """Test XSS attack prevention."""
    
    def test_petition_title_escapes_html(self):
        """Test that HTML in title is escaped."""
        petition = PetitionFactory(
            status='active',
            title='<script>alert("XSS")</script>Test'
        )
        
        client = Client()
        url = f'/peticoes/{petition.id}/{petition.slug}/'
        response = client.get(url)
        
        # Should be escaped
        assert '<script>' not in response.content.decode()
        assert '&lt;script&gt;' in response.content.decode()
    
    def test_petition_description_escapes_html(self):
        """Test that HTML in description is escaped."""
        petition = PetitionFactory(
            status='active',
            description='<img src=x onerror=alert(1)>' + 'A' * 100
        )
        
        client = Client()
        url = f'/peticoes/{petition.id}/{petition.slug}/'
        response = client.get(url)
        
        # Should be escaped
        assert 'onerror=' not in response.content.decode()
```

---

## Test Data and Fixtures

### Factory Boy Factories

```python
# pressionaapp/tests/factories.py

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from pressionaapp.models import Category, Petition, Signature
from faker import Faker

fake = Faker('pt_BR')
User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    first_name = factory.Faker('first_name', locale='pt_BR')
    last_name = factory.Faker('last_name', locale='pt_BR')


class CategoryFactory(DjangoModelFactory):
    """Factory for Category model."""
    
    class Meta:
        model = Category
    
    name = factory.Iterator([
        'Saúde', 'Educação', 'Meio Ambiente', 'Transporte',
        'Segurança', 'Cultura', 'Direitos Humanos', 'Economia'
    ])
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    is_active = True


class PetitionFactory(DjangoModelFactory):
    """Factory for Petition model."""
    
    class Meta:
        model = Petition
    
    title = factory.Faker('sentence', nb_words=6, locale='pt_BR')
    description = factory.Faker('text', max_nb_chars=500, locale='pt_BR')
    creator = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    signature_goal = factory.Faker('random_int', min=100, max=10000)
    status = 'active'
    content_hash = factory.Faker('sha256')


class SignatureFactory(DjangoModelFactory):
    """Factory for Signature model."""
    
    class Meta:
        model = Signature
    
    petition = factory.SubFactory(PetitionFactory)
    name = factory.Faker('name', locale='pt_BR')
    cpf_hash = factory.Faker('sha256')
    email = factory.Faker('email', locale='pt_BR')
    city = factory.Faker('city', locale='pt_BR')
    state = factory.Faker('estado_sigla', locale='pt_BR')
    verification_status = 'pending'
```

### Test Fixtures

```python
# pressionaapp/tests/conftest.py

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    pdf_content = b'%PDF-1.4\n' + b'Sample PDF content' * 100
    return SimpleUploadedFile(
        "test.pdf",
        pdf_content,
        content_type="application/pdf"
    )


@pytest.fixture
def authenticated_client(django_user_model):
    """Create an authenticated client."""
    from django.test import Client
    from pressionaapp.tests.factories import UserFactory
    
    user = UserFactory()
    client = Client()
    client.force_login(user)
    return client, user


@pytest.fixture
def active_petition():
    """Create an active petition for testing."""
    from pressionaapp.tests.factories import PetitionFactory
    return PetitionFactory(status='active')
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml

name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_pressiona
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run linting
      run: |
        pip install flake8
        flake8 pressionaapp --max-line-length=100
    
    - name: Run security checks
      run: |
        bandit -r pressionaapp -ll
        safety check
    
    - name: Run unit tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_pressiona
      run: |
        pytest -m unit --cov=pressionaapp --cov-report=xml
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_pressiona
      run: |
        pytest -m integration --cov=pressionaapp --cov-append --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

## Test Coverage Goals

### Coverage Targets

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| Models | 95% | High |
| Validators | 100% | High |
| Services | 90% | High |
| Views | 85% | Medium |
| Utils | 90% | Medium |
| Forms | 85% | Medium |
| Middleware | 80% | Low |

### Excluded from Coverage

```python
# .coveragerc

[run]
source = pressionaapp
omit =
    */migrations/*
    */tests/*
    */settings*.py
    */wsgi.py
    */asgi.py
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

---

## Running Tests

### Quick Commands

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage
pytest --cov=pressionaapp --cov-report=html

# Parallel execution
pytest -n auto

# Specific test file
pytest pressionaapp/tests/test_models.py

# Specific test class
pytest pressionaapp/tests/test_models.py::TestPetitionModel

# Specific test method
pytest pressionaapp/tests/test_models.py::TestPetitionModel::test_create_petition

# Verbose output
pytest -vv

# Stop on first failure
pytest -x

# Re-run failed tests
pytest --lf
```

---

**Document Status:** Complete. Ready for Phase 8: Deployment Checklist.
