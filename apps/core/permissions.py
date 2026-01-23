"""
Custom permissions for Petição Brasil.
Defines granular permissions for moderators and administrators.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_moderator_group():
    """
    Create a Moderator group with specific permissions.
    Moderators can review signatures and petitions but cannot delete or modify system settings.
    """
    # Create or get the moderator group
    moderator_group, created = Group.objects.get_or_create(name='Moderadores')
    
    if created:
        # Get content types
        from apps.signatures.models import Signature
        from apps.petitions.models import Petition, FlaggedContent
        from apps.core.models import ModerationLog
        
        signature_ct = ContentType.objects.get_for_model(Signature)
        petition_ct = ContentType.objects.get_for_model(Petition)
        flagged_ct = ContentType.objects.get_for_model(FlaggedContent)
        moderation_ct = ContentType.objects.get_for_model(ModerationLog)
        
        # Define permissions for moderators
        permissions = [
            # Signatures - can view and change, but not delete
            Permission.objects.get(codename='view_signature', content_type=signature_ct),
            Permission.objects.get(codename='change_signature', content_type=signature_ct),
            
            # Petitions - can view and change, but not delete
            Permission.objects.get(codename='view_petition', content_type=petition_ct),
            Permission.objects.get(codename='change_petition', content_type=petition_ct),
            
            # Flagged Content - full access
            Permission.objects.get(codename='view_flaggedcontent', content_type=flagged_ct),
            Permission.objects.get(codename='change_flaggedcontent', content_type=flagged_ct),
            
            # Moderation Log - view only
            Permission.objects.get(codename='view_moderationlog', content_type=moderation_ct),
        ]
        
        # Add permissions to group
        moderator_group.permissions.set(permissions)
        
        return moderator_group, True
    
    return moderator_group, False


def create_admin_group():
    """
    Create an Admin group with full permissions.
    Admins have all permissions including delete and system settings.
    """
    admin_group, created = Group.objects.get_or_create(name='Administradores')
    
    if created:
        # Admins get all permissions for the app
        from apps.signatures.models import Signature
        from apps.petitions.models import Petition, FlaggedContent
        from apps.core.models import ModerationLog, Category
        
        signature_ct = ContentType.objects.get_for_model(Signature)
        petition_ct = ContentType.objects.get_for_model(Petition)
        flagged_ct = ContentType.objects.get_for_model(FlaggedContent)
        moderation_ct = ContentType.objects.get_for_model(ModerationLog)
        category_ct = ContentType.objects.get_for_model(Category)
        
        # All permissions
        permissions = list(Permission.objects.filter(
            content_type__in=[signature_ct, petition_ct, flagged_ct, moderation_ct, category_ct]
        ))
        
        admin_group.permissions.set(permissions)
        
        return admin_group, True
    
    return admin_group, False


def assign_user_to_group(user, group_name):
    """
    Assign a user to a specific group.
    
    Args:
        user: User instance
        group_name: Name of the group ('Moderadores' or 'Administradores')
    
    Returns:
        bool: True if user was added, False if already in group
    """
    try:
        group = Group.objects.get(name=group_name)
        if group not in user.groups.all():
            user.groups.add(group)
            return True
        return False
    except Group.DoesNotExist:
        return False


def has_moderator_permission(user):
    """
    Check if user has moderator permissions.
    """
    return user.is_staff and (
        user.groups.filter(name__in=['Moderadores', 'Administradores']).exists() or
        user.is_superuser
    )


def has_admin_permission(user):
    """
    Check if user has admin permissions.
    """
    return user.is_staff and (
        user.groups.filter(name='Administradores').exists() or
        user.is_superuser
    )
