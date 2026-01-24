"""
Custom storage backends for AWS S3.
Separates media files with different permissions and cache settings.
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage backend for user-uploaded media files.
    Includes petition PDFs and signature PDFs.
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'  # Explicitly set public read ACL
    querystring_auth = False  # Files are public, no signed URLs needed
    
    # Custom cache control for different file types
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        
        # Petition PDFs - cache for 7 days (they don't change)
        # Note: name might or might not include 'media/' prefix depending on storage backend
        if 'petitions/' in name:
            params['CacheControl'] = 'max-age=604800, public'  # 7 days
        
        # Signature PDFs - cache for 24 hours (may be updated)
        elif 'signatures/' in name:
            params['CacheControl'] = 'max-age=86400, public'  # 24 hours
        
        # Other media - standard cache
        else:
            params['CacheControl'] = 'max-age=3600, public'  # 1 hour
        
        # Set content disposition for PDFs (inline display)
        if name.endswith('.pdf'):
            params['ContentDisposition'] = 'inline'
            params['ContentType'] = 'application/pdf'
        
        return params


class PrivateMediaStorage(S3Boto3Storage):
    """
    Storage backend for private files that require authentication.
    Uses signed URLs with expiration.
    """
    location = 'private'
    file_overwrite = False
    default_acl = None  # ACLs disabled - use bucket policy instead
    querystring_auth = True  # Generate signed URLs
    querystring_expire = 3600  # URLs expire in 1 hour
    
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        
        # No caching for private files
        params['CacheControl'] = 'no-cache, no-store, must-revalidate'
        
        # Force download for private files
        if name.endswith('.pdf'):
            params['ContentDisposition'] = 'attachment'
            params['ContentType'] = 'application/pdf'
        
        return params
