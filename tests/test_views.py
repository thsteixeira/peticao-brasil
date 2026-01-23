"""
Integration tests for views
"""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from apps.petitions.models import Petition
from apps.signatures.models import Signature
from tests.factories import UserFactory, PetitionFactory, SignatureFactory, CategoryFactory


@pytest.mark.integration
@pytest.mark.django_db
class TestPetitionViews:
    """Test petition view workflows"""
    
    def test_home_page_loads(self, api_client):
        """Test home page loads successfully"""
        url = reverse('petitions:home')
        response = api_client.get(url)
        assert response.status_code == 200
    
    def test_petition_list_shows_active_petitions(self, api_client):
        """Test petition list shows only active petitions"""
        active_petition = PetitionFactory(status='active')
        draft_petition = PetitionFactory(status='draft')
        
        url = reverse('petitions:petition_list')
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert active_petition.title in response.content.decode()
        assert draft_petition.title not in response.content.decode()
    
    def test_petition_detail_view(self, api_client, petition):
        """Test petition detail page loads"""
        url = reverse('petitions:petition_detail', args=[petition.slug])
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert petition.title in response.content.decode()
        assert petition.description in response.content.decode()
    
    def test_create_petition_requires_authentication(self, api_client):
        """Test creating petition requires login"""
        url = reverse('petitions:petition_create')
        response = api_client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_create_petition_authenticated(self, authenticated_client, category):
        """Test authenticated user can access create form"""
        url = reverse('petitions:petition_create')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_petition_creation_workflow(self, authenticated_client, category):
        """Test complete petition creation"""
        url = reverse('petitions:petition_create')
        data = {
            'title': 'New Test Petition',
            'description': 'This is a test petition with enough content to pass validation.',
            'category': category.id,
            'signature_goal': 1000,
        }
        
        response = authenticated_client.post(url, data)
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Petition should be created
        petition = Petition.objects.filter(title='New Test Petition').first()
        assert petition is not None
        assert petition.status == 'draft'  # New petitions start as draft
        assert petition.creator == authenticated_client.handler._force_user


@pytest.mark.integration
@pytest.mark.django_db
class TestSignatureViews:
    """Test signature submission workflow"""
    
    def test_signature_form_loads(self, api_client, petition):
        """Test signature form page loads"""
        url = reverse('signatures:signature_submit', args=[petition.slug])
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_signature_submission(self, api_client, petition):
        """Test signature submission creates pending signature"""
        url = reverse('signatures:signature_submit', args=[petition.slug])
        data = {
            'full_name': 'Maria Santos',
            'cpf': '98765432100',
            'email': 'maria@example.com',
            'city': 'Brasília',
            'state': 'DF',
            'display_name_publicly': True,
            'receive_updates': True,
        }
        
        response = api_client.post(url, data)
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Signature should be created
        signature = Signature.objects.filter(email='maria@example.com').first()
        assert signature is not None
        assert signature.petition == petition
        assert signature.verification_status == 'pending'
    
    def test_my_signatures_requires_auth(self, api_client):
        """Test my signatures page requires login"""
        url = reverse('signatures:my_signatures')
        response = api_client.get(url)
        
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.integration
@pytest.mark.django_db
class TestSearchFunctionality:
    """Test search features"""
    
    def test_petition_search_by_title(self, api_client):
        """Test searching petitions by title"""
        petition1 = PetitionFactory(title='Save the Amazon Forest', status='active')
        petition2 = PetitionFactory(title='Improve Education Quality', status='active')
        
        url = reverse('petitions:petition_list')
        response = api_client.get(url, {'q': 'Amazon'})
        
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Amazon' in content
        assert 'Education' not in content
    
    def test_petition_filter_by_category(self, api_client):
        """Test filtering petitions by category"""
        category1 = CategoryFactory(name='Saúde')
        category2 = CategoryFactory(name='Educação')
        
        petition1 = PetitionFactory(category=category1, status='active')
        petition2 = PetitionFactory(category=category2, status='active')
        
        url = reverse('petitions:petition_list')
        response = api_client.get(url, {'category': category1.slug})
        
        assert response.status_code == 200
        content = response.content.decode()
        assert petition1.title in content
