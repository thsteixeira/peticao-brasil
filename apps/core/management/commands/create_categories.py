"""
Management command to create initial categories for petitions.
"""
from django.core.management.base import BaseCommand
from apps.core.models import Category


class Command(BaseCommand):
    help = 'Create initial petition categories'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Saúde',
                'description': 'Petições relacionadas à saúde pública, hospitais, medicamentos e bem-estar',
                'icon': 'heart',
                'color': '#DC2626',
                'order': 1
            },
            {
                'name': 'Educação',
                'description': 'Petições sobre escolas, universidades, ensino e educação',
                'icon': 'book',
                'color': '#2563EB',
                'order': 2
            },
            {
                'name': 'Meio Ambiente',
                'description': 'Petições sobre sustentabilidade, preservação ambiental e ecologia',
                'icon': 'tree',
                'color': '#059669',
                'order': 3
            },
            {
                'name': 'Segurança Pública',
                'description': 'Petições relacionadas à segurança, policiamento e ordem pública',
                'icon': 'shield',
                'color': '#7C3AED',
                'order': 4
            },
            {
                'name': 'Transporte',
                'description': 'Petições sobre transporte público, mobilidade urbana e infraestrutura',
                'icon': 'bus',
                'color': '#EA580C',
                'order': 5
            },
            {
                'name': 'Direitos Humanos',
                'description': 'Petições sobre igualdade, justiça social e direitos fundamentais',
                'icon': 'users',
                'color': '#DB2777',
                'order': 6
            },
            {
                'name': 'Cultura',
                'description': 'Petições relacionadas a arte, cultura, patrimônio e eventos culturais',
                'icon': 'palette',
                'color': '#CA8A04',
                'order': 7
            },
            {
                'name': 'Economia',
                'description': 'Petições sobre emprego, economia, impostos e desenvolvimento',
                'icon': 'chart',
                'color': '#0891B2',
                'order': 8
            },
            {
                'name': 'Infraestrutura',
                'description': 'Petições sobre obras públicas, saneamento e desenvolvimento urbano',
                'icon': 'building',
                'color': '#64748B',
                'order': 9
            },
            {
                'name': 'Tecnologia',
                'description': 'Petições sobre inovação, internet, privacidade digital e tecnologia',
                'icon': 'laptop',
                'color': '#6366F1',
                'order': 10
            },
            {
                'name': 'Outros',
                'description': 'Outras causas que não se enquadram nas categorias acima',
                'icon': 'ellipsis',
                'color': '#71717A',
                'order': 99
            },
        ]

        created_count = 0
        updated_count = 0

        for cat_data in categories:
            category, created = Category.objects.update_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Categoria criada: {category.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Categoria atualizada: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Concluído! {created_count} categorias criadas, {updated_count} atualizadas.'
            )
        )
