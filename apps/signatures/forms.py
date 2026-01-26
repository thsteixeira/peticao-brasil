"""
Forms for signature submission.
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from apps.core.validators import validate_pdf_file, sanitize_filename, calculate_file_hash, validate_turnstile_token
from .models import Signature


def validate_cpf(cpf):
    """
    Validate Brazilian CPF number.
    """
    if not cpf:
        raise ValidationError('CPF é obrigatório.')
    
    # Remove non-numeric characters
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Check if CPF has 11 digits
    if len(cpf) != 11:
        raise ValidationError('CPF deve conter 11 dígitos.')
    
    # Check if all digits are the same (invalid CPF)
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    
    # Validate first check digit
    sum_digits = sum(int(cpf[i]) * (10 - i) for i in range(9))
    first_check = (sum_digits * 10) % 11
    if first_check == 10:
        first_check = 0
    if first_check != int(cpf[9]):
        raise ValidationError('CPF inválido.')
    
    # Validate second check digit
    sum_digits = sum(int(cpf[i]) * (11 - i) for i in range(10))
    second_check = (sum_digits * 10) % 11
    if second_check == 10:
        second_check = 0
    if second_check != int(cpf[10]):
        raise ValidationError('CPF inválido.')
    
    return cpf


class SignatureSubmissionForm(forms.ModelForm):
    """
    Form for submitting a signed PDF.
    """
    cpf = forms.CharField(
        max_length=14,
        label='CPF',
        help_text='Seu CPF (utilizado no certificado digital)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '000.000.000-00',
            'maxlength': '14'
        })
    )
    
    full_name = forms.CharField(
        max_length=200,
        label='Nome Completo',
        help_text='Nome completo conforme certificado digital',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Digite seu nome completo'
        })
    )
    
    email = forms.EmailField(
        label='E-mail',
        help_text='Para recebimento de confirmação',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'seu@email.com'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        label='Cidade',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Sua cidade'
        })
    )
    
    state = forms.ChoiceField(
        choices=Signature.STATES,
        label='Estado',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    signed_pdf = forms.FileField(
        label='PDF Assinado',
        help_text='Arquivo PDF assinado digitalmente (máx. 10MB)',
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'accept': '.pdf'
        })
    )
    
    accept_terms = forms.BooleanField(
        label='Aceito os Termos de Uso e Política de Privacidade',
        required=True,
        error_messages={
            'required': 'Você deve aceitar os Termos de Uso e Política de Privacidade para assinar a petição.'
        },
        widget=forms.CheckboxInput(attrs={
            'class': 'h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )
    
    turnstile_token = forms.CharField(
        widget=forms.HiddenInput(),
        required=False  # Will be set dynamically in __init__
    )    
    class Meta:
        model = Signature
        fields = ['full_name', 'email', 'city', 'state', 'signed_pdf']
    
    def __init__(self, *args, **kwargs):
        self.petition = kwargs.pop('petition', None)
        self.request = kwargs.pop('request', None)  # To get IP address
        super().__init__(*args, **kwargs)
        
        # Make Turnstile token required if enabled
        from django.conf import settings
        if settings.TURNSTILE_ENABLED:
            self.fields['turnstile_token'].required = True
    
    def clean_cpf(self):
        """Validate and clean CPF."""
        cpf = self.cleaned_data.get('cpf', '')
        validated_cpf = validate_cpf(cpf)
        return validated_cpf
    
    def clean_full_name(self):
        """Clean and validate full name."""
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 3:
            raise ValidationError('Nome completo deve ter pelo menos 3 caracteres.')
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', name):
            raise ValidationError('Nome deve conter apenas letras.')
        return name
    
    def clean_signed_pdf(self):
        """Validate uploaded PDF file."""
        pdf_file = self.cleaned_data.get('signed_pdf')
        
        if not pdf_file:
            raise ValidationError('Arquivo PDF é obrigatório.')
        
        # Use comprehensive PDF validation
        try:
            validate_pdf_file(pdf_file)
        except ValidationError:
            raise
        
        # Sanitize filename
        pdf_file.name = sanitize_filename(pdf_file.name)
        
        # Calculate file hash for integrity checking
        file_hash = calculate_file_hash(pdf_file)
        
        # Store hash in form for later use
        self.cleaned_data['file_hash'] = file_hash
        
        return pdf_file
    
    def clean(self):
        """Additional cross-field validation."""
        cleaned_data = super().clean()
        
        # Validate Turnstile token
        turnstile_token = cleaned_data.get('turnstile_token')
        remote_ip = None
        if self.request:
            remote_ip = self.request.META.get('REMOTE_ADDR')
        
        try:
            validate_turnstile_token(turnstile_token, remote_ip)
        except ValidationError as e:
            self.add_error('turnstile_token', e)
        
        # Check if petition already has a signature from this CPF
        cpf = cleaned_data.get('cpf')
        
        if cpf and self.petition:
            cpf_hash = Signature.hash_cpf(cpf)
            if Signature.objects.filter(petition=self.petition, cpf_hash=cpf_hash).exists():
                raise ValidationError('Você já assinou esta petição com este CPF.')
        
        return cleaned_data
