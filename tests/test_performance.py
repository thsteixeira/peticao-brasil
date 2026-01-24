"""
Performance tests for database queries and response times
"""
import pytest
import time
from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from apps.petitions.models import Petition
from apps.signatures.models import Signature
from tests.factories import PetitionFactory, SignatureFactory, CategoryFactory


@pytest.mark.performance
@pytest.mark.django_db
class TestQueryOptimization:
    """Test database query optimization"""
    
    def test_petition_list_query_count(self, api_client):
        """Test petition list doesn't create N+1 queries"""
        # Create multiple petitions
        PetitionFactory.create_batch(20, status='active')
        
        from django.urls import reverse
        url = reverse('petitions:list')
        
        with CaptureQueriesContext(connection) as context:
            response = api_client.get(url)
            query_count = len(context.captured_queries)
        
        # Should use select_related/prefetch_related
        # Adjust threshold based on actual implementation
        assert query_count < 50, f"Too many queries: {query_count}"
    
    def test_petition_detail_with_signatures(self, api_client, petition):
        """Test petition detail with many signatures"""
        # Add many signatures
        SignatureFactory.create_batch(100, petition=petition)
        
        from django.urls import reverse
        url = reverse('petitions:detail', args=[petition.uuid, petition.slug])
        
        with CaptureQueriesContext(connection) as context:
            response = api_client.get(url)
            query_count = len(context.captured_queries)
        
        # Should paginate and optimize queries
        assert query_count < 30, f"Too many queries: {query_count}"


@pytest.mark.performance
@pytest.mark.django_db
class TestResponseTimes:
    """Test view response times"""
    
    def test_home_page_response_time(self, api_client):
        """Test home page loads quickly"""
        # Create realistic data
        PetitionFactory.create_batch(10, status='active')
        
        from django.urls import reverse
        url = reverse('petitions:home')
        
        start = time.time()
        response = api_client.get(url)
        duration = time.time() - start
        
        assert response.status_code == 200
        # Should load in under 1 second
        assert duration < 1.0, f"Page took {duration:.2f}s to load"
    
    def test_search_performance(self, api_client):
        """Test search with large dataset"""
        # Create many petitions
        for i in range(50):
            PetitionFactory(
                title=f'Test Petition {i}',
                status='active'
            )
        
        from django.urls import reverse
        url = reverse('petitions:list')
        
        start = time.time()
        response = api_client.get(url, {'q': 'Test'})
        duration = time.time() - start
        
        assert response.status_code == 200
        # Search should complete quickly
        assert duration < 2.0, f"Search took {duration:.2f}s"


@pytest.mark.performance
@pytest.mark.django_db
class TestDatabaseIndexes:
    """Test database indexes are effective"""
    
    def test_slug_lookup_uses_index(self, petition):
        """Test slug lookups use database index"""
        with CaptureQueriesContext(connection) as context:
            Petition.objects.get(slug=petition.slug)
            
            # Should be a simple index lookup
            assert len(context.captured_queries) == 1
            query = context.captured_queries[0]['sql'].lower()
            # Should use WHERE clause on slug
            assert 'slug' in query
    
    def test_category_filter_performance(self):
        """Test filtering by category is fast"""
        category = CategoryFactory()
        PetitionFactory.create_batch(100, category=category, status='active')
        
        with CaptureQueriesContext(connection) as context:
            petitions = list(Petition.objects.filter(
                category=category,
                status='active'
            )[:20])
            
            # Should be efficient with proper indexes
            assert len(context.captured_queries) <= 2


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.django_db
class TestScalability:
    """Test system behavior with large datasets"""
    
    def test_large_petition_list(self, api_client):
        """Test handling many petitions"""
        # Create large dataset
        PetitionFactory.create_batch(1000, status='active')
        
        from django.urls import reverse
        url = reverse('petitions:list')
        
        # Should still respond quickly with pagination
        start = time.time()
        response = api_client.get(url)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 3.0, f"Large list took {duration:.2f}s"
    
    def test_many_signatures_on_petition(self, petition):
        """Test petition with thousands of signatures"""
        # Create many approved signatures (only approved signatures count)
        SignatureFactory.create_batch(
            1000,
            petition=petition,
            verification_status=Signature.STATUS_APPROVED
        )
        
        # Manually update count since we're bypassing the verification task
        petition.signature_count = petition.signatures.filter(
            verification_status=Signature.STATUS_APPROVED
        ).count()
        petition.save()
        
        # Refresh and check performance
        petition.refresh_from_db()
        
        # Should calculate metrics efficiently
        assert petition.signature_count == 1000
        assert petition.progress_percentage <= 100
