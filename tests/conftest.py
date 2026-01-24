"""
Pytest configuration and fixtures for the test suite.
"""
import pytest
import io
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.core.models import Category
from apps.petitions.models import Petition
from apps.signatures.models import Signature

User = get_user_model()


# Disable Turnstile validation for tests
@pytest.fixture(autouse=True)
def disable_turnstile(settings):
    """Disable Turnstile validation for all tests"""
    settings.TURNSTILE_ENABLED = False
    # Also disable Celery async tasks to prevent auto-verification
    settings.CELERY_TASK_ALWAYS_EAGER = False
    return settings


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def category(db):
    """Create a test category"""
    return Category.objects.create(
        name='Saúde',
        slug='saude',
        description='Petições sobre saúde pública',
        icon='🏥',
        color='#28a745',
        active=True,
        order=1
    )


@pytest.fixture
def petition(db, user, category):
    """Create a test petition"""
    return Petition.objects.create(
        creator=user,
        category=category,
        title='Test Petition',
        description='This is a test petition description',
        signature_goal=1000,
        status=Petition.STATUS_ACTIVE,
        is_active=True
    )


@pytest.fixture
def completed_petition(db, user, category):
    """Create a completed petition"""
    petition = Petition.objects.create(
        creator=user,
        category=category,
        title='Completed Petition',
        description='This petition has reached its goal',
        signature_goal=100,
        signature_count=150,
        status=Petition.STATUS_COMPLETED,
        is_active=True
    )
    return petition


@pytest.fixture
def signature(db, petition):
    """Create a test signature"""
    return Signature.objects.create(
        petition=petition,
        full_name='João Silva',
        cpf_hash=Signature.hash_cpf('12345678901'),
        email='joao@example.com',
        city='São Paulo',
        state='SP',
        verification_status=Signature.STATUS_PENDING
    )


@pytest.fixture
def approved_signature(db, petition):
    """Create an approved signature"""
    return Signature.objects.create(
        petition=petition,
        full_name='Maria Santos',
        cpf_hash=Signature.hash_cpf('98765432100'),
        email='maria@example.com',
        city='Rio de Janeiro',
        state='RJ',
        verification_status=Signature.STATUS_APPROVED
    )


@pytest.fixture
def api_client():
    """Create a Django test client"""
    from django.test import Client
    return Client()


@pytest.fixture
def authenticated_client(db, user):
    """Create an authenticated client"""
    from django.test import Client
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(db, admin_user):
    """Create an admin client"""
    from django.test import Client
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file for testing"""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    return SimpleUploadedFile(
        "test.pdf",
        pdf_content,
        content_type="application/pdf"
    )
