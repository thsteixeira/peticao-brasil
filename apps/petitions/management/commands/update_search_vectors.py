"""
Django management command to update search vectors for all petitions.
Usage: python manage.py update_search_vectors
"""
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from apps.petitions.models import Petition


class Command(BaseCommand):
    help = 'Update search vectors for all petitions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all petitions (including inactive)',
        )

    def handle(self, *args, **options):
        if options['all']:
            petitions = Petition.objects.all()
            self.stdout.write('Updating search vectors for ALL petitions...')
        else:
            petitions = Petition.objects.filter(is_active=True)
            self.stdout.write('Updating search vectors for active petitions...')
        
        total = petitions.count()
        self.stdout.write(f'Total petitions to update: {total}')
        
        # Update in bulk
        petitions.update(
            search_vector=SearchVector('title', weight='A') + 
                         SearchVector('description', weight='B') +
                         SearchVector('category__name', weight='C')
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully updated {total} petition search vectors!')
        )
