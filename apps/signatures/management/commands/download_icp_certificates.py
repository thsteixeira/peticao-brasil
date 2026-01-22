"""
Management command to download ICP-Brasil root certificates.
"""
import os
import urllib.request
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Download ICP-Brasil root certificates for signature verification'

    # Active ICP-Brasil root certificates as of 2026
    CERTIFICATES = {
        'ICP-Brasilv4.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv4.crt',
        'ICP-Brasilv5.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv5.crt',
        'ICP-Brasilv6.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv6.crt',
        'ICP-Brasilv7.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv7.crt',
        'ICP-Brasilv10.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv10.crt',
        'ICP-Brasilv11.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv11.crt',
        'ICP-Brasilv12.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv12.crt',
        'ICP-Brasilv13.crt': 'https://acraiz.icpbrasil.gov.br/credenciadas/RAIZ/ICP-Brasilv13.crt',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-download of existing certificates',
        )

    def handle(self, *args, **options):
        # Get the certificate storage directory
        cert_dir = os.path.join(
            settings.BASE_DIR,
            'apps',
            'signatures',
            'icp_certificates'
        )
        
        # Create directory if it doesn't exist
        os.makedirs(cert_dir, exist_ok=True)
        
        self.stdout.write(f'Downloading ICP-Brasil certificates to: {cert_dir}\n')
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for filename, url in self.CERTIFICATES.items():
            filepath = os.path.join(cert_dir, filename)
            
            # Skip if file exists and not forcing
            if os.path.exists(filepath) and not options['force']:
                self.stdout.write(
                    self.style.WARNING(f'⊘ [{filename}] Already exists (use --force to re-download)')
                )
                skip_count += 1
                continue
            
            try:
                self.stdout.write(f'Downloading {filename}...')
                
                # Download the certificate
                with urllib.request.urlopen(url, timeout=30) as response:
                    cert_data = response.read()
                
                # Save to file
                with open(filepath, 'wb') as f:
                    f.write(cert_data)
                
                file_size = len(cert_data)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ [{filename}] Downloaded ({file_size} bytes)')
                )
                success_count += 1
                
            except urllib.error.URLError as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ [{filename}] Network error: {str(e)}')
                )
                error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ [{filename}] Error: {str(e)}')
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(f'Downloaded: {success_count}') + ' | ' +
            self.style.WARNING(f'Skipped: {skip_count}') + ' | ' +
            self.style.ERROR(f'Errors: {error_count}')
        )
        
        if error_count == 0 and success_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Certificate download complete!')
            )
        elif error_count > 0:
            self.stdout.write(
                self.style.WARNING('\n⚠ Some certificates failed to download')
            )
