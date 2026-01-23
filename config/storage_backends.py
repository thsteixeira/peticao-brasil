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
    default_acl = 'public-read'  # Make files publicly accessible
    querystring_auth = False  # Don't use signed URLs for public files
    
    # Custom cache control for different file types
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        
        # Petition PDFs - cache for 7 days (they don't change)
        if name.startswith('media/petitions/'):
            params['CacheControl'] = 'max-age=604800, public'  # 7 days
            params['ACL'] = 'public-read'  # Explicitly public
        
        # Signature PDFs - cache for 24 hours (may be updated)
        elif name.startswith('media/signatures/'):
            params['CacheControl'] = 'max-age=86400, public'  # 24 hours
            params['ACL'] = 'public-read'  # Explicitly public
        
        # Other media - standard cache
        else:
            params['CacheControl'] = 'max-age=3600, public'  # 1 hour
            params['ACL'] = 'public-read'
        
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
