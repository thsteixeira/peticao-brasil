"""
Security tests for XSS, injection, and file upload protection
"""
import pytest
from django.test import Client
from django.urls import reverse
from apps.petitions.models import Petition
from apps.signatures.models import Signature
from tests.factories import UserFactory, CategoryFactory, PetitionFactory


@pytest.mark.security
@pytest.mark.django_db
class TestXSSPrevention:
    """Test XSS attack prevention"""
    
    def test_xss_in_petition_title(self, authenticated_client, category):
        """Test XSS in petition title is sanitized"""
        url = reverse('petitions:petition_create')
        data = {
            'title': '<script>alert("XSS")</script>Legitimate Title',
            'description': 'Valid description content.',
            'category': category.id,
            'signature_goal': 1000,
        }
        
        response = authenticated_client.post(url, data)
        
        if response.status_code == 302:  # Successful creation
            petition = Petition.objects.latest('created_at')
            # Script tag should be removed or escaped
            assert '<script>' not in petition.title
            assert 'Legitimate Title' in petition.title
    
    def test_xss_in_petition_description(self, authenticated_client, category):
        """Test XSS in description is sanitized"""
        url = reverse('petitions:petition_create')
        data = {
            'title': 'Test Petition',
            'description': '<img src=x onerror="alert(1)">Valid content',
            'category': category.id,
            'signature_goal': 1000,
        }
        
        response = authenticated_client.post(url, data)
        
        if response.status_code == 302:
            petition = Petition.objects.latest('created_at')
            # Malicious attributes should be removed
            assert 'onerror=' not in petition.description
            assert 'Valid content' in petition.description
    
    def test_xss_in_signature_name(self, api_client, petition):
        """Test XSS in signature full name is sanitized"""
        url = reverse('signatures:signature_submit', args=[petition.slug])
        data = {
            'full_name': '<script>alert("XSS")</script>John Doe',
            'cpf': '12345678909',
            'email': 'test@example.com',
            'city': 'São Paulo',
            'state': 'SP',
        }
        
        response = api_client.post(url, data)
        
        # Should either reject or sanitize
        if response.status_code == 302:
            signature = Signature.objects.latest('created_at')
            assert '<script>' not in signature.full_name


@pytest.mark.security
@pytest.mark.django_db
class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""
    
    def test_sql_injection_in_search(self, api_client):
        """Test SQL injection in search query"""
        url = reverse('petitions:petition_list')
        
        # Attempt SQL injection
        malicious_queries = [
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "'; DROP TABLE petitions--",
        ]
        
        for query in malicious_queries:
            response = api_client.get(url, {'q': query})
            # Should return normal response, not error
            assert response.status_code == 200
    
    def test_sql_injection_in_cpf_lookup(self, api_client, petition):
        """Test SQL injection in CPF field"""
        url = reverse('signatures:signature_submit', args=[petition.slug])
        data = {
            'full_name': 'John Doe',
            'cpf': "12345678909' OR '1'='1",
            'email': 'test@example.com',
            'city': 'São Paulo',
            'state': 'SP',
        }
        
        response = api_client.post(url, data)
        # Should reject invalid CPF, not execute injection
        assert response.status_code in [200, 400, 302]


@pytest.mark.security
@pytest.mark.django_db
class TestFileUploadSecurity:
    """Test file upload security"""
    
    def test_pdf_file_type_validation(self, authenticated_client):
        """Test only PDF files are accepted for signatures"""
        # This would test certificate upload if implemented
        # For now, placeholder for future file upload tests
        pass
    
    def test_file_size_limit(self, authenticated_client):
        """Test file size limits are enforced"""
        # Placeholder for file size validation tests
        pass
    
    def test_malicious_filename(self, authenticated_client):
        """Test malicious filenames are sanitized"""
        # Test filenames like '../../../etc/passwd'
        pass


@pytest.mark.security
@pytest.mark.django_db
class TestAuthenticationSecurity:
    """Test authentication and authorization"""
    
    def test_csrf_protection(self, api_client, category):
        """Test CSRF protection is active"""
        url = reverse('petitions:petition_create')
        
        # Attempt POST without CSRF token
        data = {
            'title': 'Test',
            'description': 'Test description',
            'category': category.id,
            'signature_goal': 1000,
        }
        
        # Should fail without proper CSRF token
        # Note: api_client bypasses CSRF, use Client() for real test
        client = Client()
        response = client.post(url, data)
        assert response.status_code in [403, 302]  # Forbidden or redirect to login
    
    def test_unauthorized_petition_edit(self, authenticated_client):
        """Test users cannot edit other users' petitions"""
        other_user = UserFactory()
        petition = PetitionFactory(creator=other_user, status='draft')
        
        url = reverse('petitions:petition_update', args=[petition.slug])
        response = authenticated_client.get(url)
        
        # Should deny access
        assert response.status_code in [403, 404]
    
    def test_unauthorized_admin_access(self, authenticated_client):
        """Test regular users cannot access admin"""
        response = authenticated_client.get('/admin/')
        
        # Should redirect or deny
        assert response.status_code in [302, 403]


@pytest.mark.security
@pytest.mark.django_db
class TestRateLimiting:
    """Test rate limiting and abuse prevention"""
    
    def test_signature_rate_limiting(self, api_client, petition):
        """Test rapid signature submissions are rate limited"""
        url = reverse('signatures:signature_submit', args=[petition.slug])
        
        # Attempt multiple rapid submissions
        for i in range(10):
            data = {
                'full_name': f'User {i}',
                'cpf': f'1234567890{i}',
                'email': f'user{i}@example.com',
                'city': 'São Paulo',
                'state': 'SP',
            }
            response = api_client.post(url, data)
        
        # Should eventually rate limit (if implemented)
        # This is a placeholder for rate limiting tests
        pass


@pytest.mark.security
@pytest.mark.django_db  
class TestDataPrivacy:
    """Test data privacy and LGPD compliance"""
    
    def test_cpf_is_hashed(self, signature):
        """Test CPF is never stored in plain text"""
        # CPF should be hashed
        assert len(signature.cpf_hash) == 64  # SHA-256 hex
        
        # Original CPF should not be retrievable
        assert not hasattr(signature, 'cpf')
    
    def test_private_signature_hides_name(self, api_client):
        """Test private signatures don't expose full names"""
        petition = PetitionFactory(status='active')
        sig = petition.signatures.create(
            full_name='João Silva Santos',
            cpf_hash='a' * 64,
            email='test@example.com',
            city='São Paulo',
            state='SP',
            display_name_publicly=False,
            verification_status='approved',
        )
        
        url = reverse('signatures:petition_signatures', args=[petition.slug])
        response = api_client.get(url)
        
        content = response.content.decode()
        # Should show initials, not full name
        assert 'J. S.' in content or 'João Silva Santos' not in content
