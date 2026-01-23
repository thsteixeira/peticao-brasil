"""
Django management command to create permission groups.
Usage: python manage.py create_permission_groups
"""
from django.core.management.base import BaseCommand
from apps.core.permissions import create_moderator_group, create_admin_group


class Command(BaseCommand):
    help = 'Create Moderador and Administrador permission groups'

    def handle(self, *args, **options):
        # Create moderator group
        moderator_group, created = create_moderator_group()
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Grupo "Moderadores" criado com sucesso')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Grupo "Moderadores" já existe')
            )
        
        # Create admin group
        admin_group, created = create_admin_group()
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Grupo "Administradores" criado com sucesso')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Grupo "Administradores" já existe')
            )
        
        # Display permission counts
        mod_perms = moderator_group.permissions.count()
        admin_perms = admin_group.permissions.count()
        
        self.stdout.write('')
        self.stdout.write(f'Moderadores: {mod_perms} permissões')
        self.stdout.write(f'Administradores: {admin_perms} permissões')
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✓ Grupos de permissão configurados com sucesso!')
        )
