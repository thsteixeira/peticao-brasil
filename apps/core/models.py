"""
Core models for the Petição Brasil application.
Contains Category model for petition categorization.
"""
import uuid
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator


class Category(models.Model):
    """
    Categories for organizing petitions by topic.
    Predefined and managed by administrators.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome",
        help_text="Nome da categoria (ex: Saúde, Educação)"
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Slug",
        help_text="URL amigável (gerado automaticamente)"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição opcional da categoria"
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ícone",
        help_text="Nome do ícone Bootstrap ou Font Awesome (ex: 'heart', 'book')"
    )
    
    color = models.CharField(
        max_length=7,
        default="#0066CC",
        verbose_name="Cor",
        help_text="Cor hexadecimal para exibição (ex: #FF5733)"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição (menor = primeiro)"
    )
    
    active = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Se desativada, não aparece para novas petições"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['active', 'order']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('petitions:category', kwargs={'slug': self.slug})
    
    @property
    def petition_count(self):
        """Count of active petitions in this category"""
        return self.petitions.filter(is_active=True).count()


class ModerationLog(models.Model):
    """
    Log of moderation actions taken by staff users.
    Tracks all approve/reject actions for audit trail.
    """
    
    ACTION_TYPES = [
        ('petition_approve', 'Petição Aprovada'),
        ('petition_reject', 'Petição Rejeitada'),
        ('petition_archive', 'Petição Arquivada'),
        ('signature_approve', 'Assinatura Aprovada'),
        ('signature_reject', 'Assinatura Rejeitada'),
        ('signature_bulk_approve', 'Assinaturas Aprovadas em Lote'),
        ('signature_bulk_reject', 'Assinaturas Rejeitadas em Lote'),
        ('user_ban', 'Usuário Banido'),
        ('user_unban', 'Usuário Desbanido'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderation_actions',
        verbose_name="Moderador"
    )
    
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        verbose_name="Tipo de Ação"
    )
    
    content_type = models.CharField(
        max_length=50,
        verbose_name="Tipo de Conteúdo",
        help_text="petition, signature, user"
    )
    
    object_id = models.CharField(
        max_length=255,
        verbose_name="ID do Objeto"
    )
    
    reason = models.TextField(
        blank=True,
        verbose_name="Motivo",
        help_text="Razão para a ação de moderação"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notas Internas",
        help_text="Notas adicionais visíveis apenas para moderadores"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Endereço IP"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Ação"
    )
    
    class Meta:
        verbose_name = "Log de Moderação"
        verbose_name_plural = "Logs de Moderação"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['moderator', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.moderator} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def log_action(cls, moderator, action_type, content_type, object_id, reason='', notes='', ip_address=None):
        """
        Helper method to create a moderation log entry.
        """
        return cls.objects.create(
            moderator=moderator,
            action_type=action_type,
            content_type=content_type,
            object_id=str(object_id),
            reason=reason,
            notes=notes,
            ip_address=ip_address
        )
