"""
Management command to generate PDF for existing petitions.
"""
from django.core.management.base import BaseCommand
from apps.petitions.models import Petition
from apps.petitions.pdf_service import PetitionPDFGenerator


class Command(BaseCommand):
    help = 'Generate PDFs for petitions that do not have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate PDFs for all petitions',
        )
        parser.add_argument(
            '--uuid',
            type=str,
            help='Generate PDF for specific petition UUID',
        )

    def handle(self, *args, **options):
        if options['uuid']:
            # Generate for specific petition
            try:
                petition = Petition.objects.get(uuid=options['uuid'])
                self.stdout.write(f'Generating PDF for petition: {petition.title}')
                pdf_url = PetitionPDFGenerator.generate_and_save(petition)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ PDF generated: {pdf_url}')
                )
            except Petition.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Petition with UUID {options["uuid"]} not found')
                )
                return
        
        elif options['all']:
            # Regenerate all PDFs
            petitions = Petition.objects.all()
            total = petitions.count()
            self.stdout.write(f'Regenerating PDFs for {total} petitions...')
            
            for i, petition in enumerate(petitions, 1):
                try:
                    pdf_url = PetitionPDFGenerator.generate_and_save(petition)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ [{i}/{total}] {petition.title}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ [{i}/{total}] {petition.title}: {str(e)}')
                    )
        
        else:
            # Generate for petitions without PDF
            petitions = Petition.objects.filter(pdf_url='')
            total = petitions.count()
            
            if total == 0:
                self.stdout.write(
                    self.style.SUCCESS('✓ All petitions already have PDFs')
                )
                return
            
            self.stdout.write(f'Generating PDFs for {total} petitions...')
            
            for i, petition in enumerate(petitions, 1):
                try:
                    pdf_url = PetitionPDFGenerator.generate_and_save(petition)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ [{i}/{total}] {petition.title}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ [{i}/{total}] {petition.title}: {str(e)}')
                    )
        
        self.stdout.write(self.style.SUCCESS('\n✓ PDF generation complete!'))
