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
