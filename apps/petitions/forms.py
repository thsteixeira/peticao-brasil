"""
Forms for petition creation and management.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from apps.core.security import validate_no_javascript, sanitize_html_input
from .models import Petition
from apps.core.models import Category


class PetitionForm(forms.ModelForm):
    """
    Form for creating and editing petitions.
    """
    
    class Meta:
        model = Petition
        fields = ['title', 'category', 'description', 'signature_goal', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Ex: Pela construção de uma nova escola no bairro',
                'maxlength': '200'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': '10',
                'placeholder': 'Descreva detalhadamente a causa da petição...',
                'maxlength': '10000'
            }),
            'signature_goal': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '10',
                'max': '1000000',
                'placeholder': '1000'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update labels to Portuguese
        self.fields['title'].label = 'Título da Petição'
        self.fields['category'].label = 'Categoria'
        self.fields['description'].label = 'Descrição Completa'
        self.fields['signature_goal'].label = 'Meta de Assinaturas'
        self.fields['deadline'].label = 'Prazo (opcional)'
        
        # Update help texts
        self.fields['title'].help_text = 'Máximo de 200 caracteres. Seja claro e objetivo.'
        self.fields['category'].help_text = 'Escolha a categoria que melhor representa sua causa.'
        self.fields['description'].help_text = 'Explique detalhadamente a causa, objetivos e justificativa. Máximo de 10.000 caracteres.'
        self.fields['signature_goal'].help_text = 'Quantas assinaturas você deseja alcançar? (mínimo 10, máximo 1.000.000)'
        self.fields['deadline'].help_text = 'Data limite para coleta de assinaturas (opcional). Mínimo 7 dias a partir de hoje.'
        
        # Filter only active categories
        self.fields['category'].queryset = Category.objects.filter(active=True)
        
        # Make deadline optional
        self.fields['deadline'].required = False
    
    def clean_title(self):
        """Clean and validate title."""
        title = self.cleaned_data.get('title', '').strip()
        
        if len(title) < 10:
            raise ValidationError('O título deve ter pelo menos 10 caracteres.')
        
        # Check for JavaScript
        validate_no_javascript(title)
        
        return title
    
    def clean_description(self):
        """Clean and validate description."""
        description = self.cleaned_data.get('description', '').strip()
        
        if len(description) < 50:
            raise ValidationError('A descrição deve ter pelo menos 50 caracteres.')
        
        # Check for JavaScript
        validate_no_javascript(description)
        
        # Sanitize HTML
        description = sanitize_html_input(description)
        
        return description
    
    def clean_signature_goal(self):
        goal = self.cleaned_data.get('signature_goal')
        if goal < 10:
            raise ValidationError('A meta deve ser de pelo menos 10 assinaturas.')
        if goal > 1000000:
            raise ValidationError('A meta não pode exceder 1.000.000 de assinaturas.')
        return goal
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline:
            min_deadline = timezone.now().date() + timedelta(days=7)
            max_deadline = timezone.now().date() + timedelta(days=365)
            
            if deadline < min_deadline:
                raise ValidationError('O prazo deve ser de pelo menos 7 dias a partir de hoje.')
            if deadline > max_deadline:
                raise ValidationError('O prazo não pode ser superior a 1 ano.')
        
        return deadline
