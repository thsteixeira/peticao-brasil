"""
Django management command to clean up old files in S3.
Usage: python manage.py cleanup_old_s3_files
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.core.s3_utils import s3_manager
from apps.signatures.models import Signature
from apps.petitions.models import Petition


class Command(BaseCommand):
    help = 'Clean up old PDF files from S3 based on retention policies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete signature PDFs older than this many days (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        if not s3_manager.use_s3:
            self.stdout.write(
                self.style.WARNING('S3 is not enabled. Nothing to clean up.')
            )
            return
        
        self.stdout.write(f'Looking for signature PDFs older than {days} days (before {cutoff_date.date()})...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be deleted'))
        
        # Find old signatures
        old_signatures = Signature.objects.filter(
            verified_at__lt=cutoff_date,
            signed_pdf__isnull=False
        ).exclude(signed_pdf='')
        
        total = old_signatures.count()
        deleted = 0
        errors = 0
        
        self.stdout.write(f'Found {total} signatures to process')
        
        for signature in old_signatures:
            file_path = signature.signed_pdf.name
            
            if dry_run:
                self.stdout.write(f'Would delete: {file_path}')
                deleted += 1
            else:
                if s3_manager.delete_file(file_path):
                    signature.signed_pdf = None
                    signature.save(update_fields=['signed_pdf'])
                    deleted += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Deleted: {file_path}')
                    )
                else:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to delete: {file_path}')
                    )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Total signatures processed: {total}'))
        self.stdout.write(self.style.SUCCESS(f'Files deleted: {deleted}'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {errors}'))
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING('This was a DRY RUN. Run without --dry-run to actually delete files.')
            )
