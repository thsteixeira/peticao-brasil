"""
S3 file management utilities for Petição Brasil.
Handles file uploads, signed URLs, and lifecycle management.
"""
from django.conf import settings
from datetime import timedelta
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class S3FileManager:
    """
    Manager for S3 file operations.
    """
    
    def __init__(self):
        self.use_s3 = getattr(settings, 'USE_S3', False)
        
        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        else:
            self.s3_client = None
            self.bucket_name = None
    
    def generate_signed_url(self, file_path, expiration=3600):
        """
        Generate a signed URL for temporary file access.
        
        Args:
            file_path: Path to file in S3 (e.g., 'media/signatures/pdfs/file.pdf')
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            str: Signed URL or regular URL if not using S3
        """
        if not self.use_s3:
            return file_path
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating signed URL: {e}")
            return None
    
    def delete_file(self, file_path):
        """
        Delete a file from S3.
        
        Args:
            file_path: Path to file in S3
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.use_s3:
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.info(f"Deleted file from S3: {file_path}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
    
    def get_file_metadata(self, file_path):
        """
        Get metadata for a file in S3.
        
        Args:
            file_path: Path to file in S3
        
        Returns:
            dict: File metadata or None if error
        """
        if not self.use_s3:
            return None
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return {
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
            }
        except ClientError as e:
            logger.error(f"Error getting file metadata: {e}")
            return None
    
    def copy_file(self, source_path, destination_path):
        """
        Copy a file within S3.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.use_s3:
            return False
        
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': source_path},
                Key=destination_path
            )
            logger.info(f"Copied file in S3: {source_path} -> {destination_path}")
            return True
        except ClientError as e:
            logger.error(f"Error copying file in S3: {e}")
            return False
    
    def set_file_permissions(self, file_path, acl='public-read'):
        """
        Set permissions for a file in S3.
        
        Args:
            file_path: Path to file in S3
            acl: ACL to apply ('private', 'public-read', 'authenticated-read')
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.use_s3:
            return False
        
        try:
            self.s3_client.put_object_acl(
                Bucket=self.bucket_name,
                Key=file_path,
                ACL=acl
            )
            logger.info(f"Set ACL for {file_path}: {acl}")
            return True
        except ClientError as e:
            logger.error(f"Error setting file permissions: {e}")
            return False
    
    def list_files_in_folder(self, prefix, max_files=1000):
        """
        List files in a specific S3 folder.
        
        Args:
            prefix: Folder prefix (e.g., 'media/signatures/')
            max_files: Maximum number of files to return
        
        Returns:
            list: List of file keys
        """
        if not self.use_s3:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_files
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            logger.error(f"Error listing files: {e}")
            return []


# Global instance
s3_manager = S3FileManager()


def get_file_url(file_field, signed=False, expiration=3600):
    """
    Get URL for a Django FileField, with optional signed URL.
    
    Args:
        file_field: Django FileField instance
        signed: Whether to generate a signed URL
        expiration: Expiration time in seconds for signed URLs
    
    Returns:
        str: File URL or None
    """
    if not file_field:
        return None
    
    if signed and s3_manager.use_s3:
        return s3_manager.generate_signed_url(file_field.name, expiration)
    
    return file_field.url if file_field else None
