"""
Pytest configuration and fixtures for the test suite.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.core.models import Category
from apps.petitions.models import Petition
from apps.signatures.models import Signature

User = get_user_model()


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
