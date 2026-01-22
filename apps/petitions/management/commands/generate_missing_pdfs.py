"""
Management command to generate PDFs for petitions that don't have them.
"""
from django.core.management.base import BaseCommand
from apps.petitions.models import Petition
from apps.petitions.pdf_service import PetitionPDFGenerator


class Command(BaseCommand):
    help = 'Generate PDFs for all petitions that are missing them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate PDFs for all petitions, even if they already have one',
        )

    def handle(self, *args, **options):
        if options['all']:
            petitions = Petition.objects.all()
            self.stdout.write('Regenerating PDFs for all petitions...')
        else:
            petitions = Petition.objects.filter(pdf_url__isnull=True) | Petition.objects.filter(pdf_url='')
            self.stdout.write('Generating PDFs for petitions without PDFs...')

        total = petitions.count()
        success = 0
        failed = 0

        for petition in petitions:
            try:
                self.stdout.write(f'Generating PDF for: {petition.title} ({petition.uuid})')
                pdf_url = PetitionPDFGenerator.generate_and_save(petition)
                self.stdout.write(self.style.SUCCESS(f'  ✓ PDF generated: {pdf_url}'))
                success += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {str(e)}'))
                failed += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  Total petitions: {total}')
        self.stdout.write(self.style.SUCCESS(f'  Successful: {success}'))
        if failed > 0:
            self.stdout.write(self.style.ERROR(f'  Failed: {failed}'))
