"""
Advanced search and filter forms for petitions.
"""
from django import forms
from django.db.models import Q
import re
from apps.core.models import Category


class PetitionSearchForm(forms.Form):
    """
    Advanced search and filter form for petitions.
    """
    
    # Text search
    q = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            'placeholder': 'Buscar petições...',
            'autocomplete': 'off',
        }),
        label='Buscar'
    )
    
    # Category filter
    categories = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Category.objects.filter(active=True).order_by('order', 'name'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'mr-2'
        }),
        label='Categorias'
    )
    
    # Status filter
    STATUS_CHOICES = [
        ('', 'Todos os status'),
        ('active', 'Ativas'),
        ('completed', 'Meta alcançada'),
        ('expiring_soon', 'Encerrando em breve'),
    ]
    
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
        }),
        label='Status'
    )
    
    # Signature count filter
    min_signatures = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            'placeholder': 'Mínimo de assinaturas'
        }),
        label='Mínimo de assinaturas'
    )
    
    # Location filters
    state = forms.CharField(
        required=False,
        max_length=2,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            'placeholder': 'UF',
            'maxlength': '2',
            'style': 'text-transform: uppercase;'
        }),
        label='Estado (UF)'
    )
    
    city = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            'placeholder': 'Cidade'
        }),
        label='Cidade'
    )
    
    # Sorting
    SORT_CHOICES = [
        ('-created_at', 'Mais recentes'),
        ('created_at', 'Mais antigas'),
        ('-signature_count', 'Mais assinadas'),
        ('signature_count', 'Menos assinadas'),
        ('deadline', 'Prazo mais próximo'),
        ('-deadline', 'Prazo mais distante'),
        ('relevance', 'Relevância (busca)'),
    ]
    
    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
        }),
        label='Ordenar por'
    )
    
    def clean_state(self):
        """Validate and normalize state"""
        state = self.cleaned_data.get('state', '').strip().upper()
        if state:
            valid_states = [
                'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
                'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
                'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
            ]
            if state not in valid_states:
                raise forms.ValidationError('Estado inválido')
        return state
