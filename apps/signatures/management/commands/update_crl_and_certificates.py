"""
Management command to download CRLs and update ICP-Brasil certificates.
"""
from django.core.management.base import BaseCommand
from apps.signatures.tasks import download_and_cache_crls, update_icp_brasil_certificates


class Command(BaseCommand):
    help = 'Download and cache CRLs, and check for new ICP-Brasil root certificates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crl-only',
            action='store_true',
            help='Only download and cache CRLs',
        )
        parser.add_argument(
            '--certs-only',
            action='store_true',
            help='Only check for new ICP-Brasil certificates',
        )

    def handle(self, *args, **options):
        crl_only = options.get('crl_only', False)
        certs_only = options.get('certs_only', False)
        
        # Download and cache CRLs
        if not certs_only:
            self.stdout.write(self.style.WARNING('\n📥 Downloading and caching CRLs...\n'))
            try:
                result = download_and_cache_crls()
                
                self.stdout.write('─' * 60)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successful: {len(result["success"])}') + 
                    f' | {", ".join(result["success"])}'
                )
                
                if result['failed']:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed: {len(result["failed"])}') +
                        f' | {", ".join([f["ca"] for f in result["failed"]])}'
                    )
                
                self.stdout.write(
                    self.style.WARNING(f'📊 Total revoked certificates cached: {result["total_revoked_certs"]}')
                )
                self.stdout.write('─' * 60)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'\n✗ CRL download failed: {str(e)}')
                )
        
        # Check for new certificates
        if not crl_only:
            self.stdout.write(self.style.WARNING('\n🔍 Checking for new ICP-Brasil certificates...\n'))
            try:
                result = update_icp_brasil_certificates()
                
                self.stdout.write('─' * 60)
                
                if result['downloaded']:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Downloaded: {len(result["downloaded"])}') +
                        f' | {", ".join(result["downloaded"])}'
                    )
                
                if result['skipped']:
                    self.stdout.write(
                        self.style.WARNING(f'⊘ Skipped (already exist): {len(result["skipped"])}')
                    )
                
                if result['failed']:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed: {len(result["failed"])}') +
                        f' | {", ".join([f["filename"] for f in result["failed"]])}'
                    )
                
                if not result['downloaded'] and not result['failed']:
                    self.stdout.write(
                        self.style.SUCCESS('✓ All certificates up to date')
                    )
                
                self.stdout.write('─' * 60)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'\n✗ Certificate update failed: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Update complete!')
        )
