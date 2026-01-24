"""
Custom password validators for strong password requirements.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """
    Validate that the password contains at least one uppercase letter.
    """
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("A senha deve conter pelo menos uma letra maiúscula (A-Z)."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Sua senha deve conter pelo menos uma letra maiúscula (A-Z).")


class LowercaseValidator:
    """
    Validate that the password contains at least one lowercase letter.
    """
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("A senha deve conter pelo menos uma letra minúscula (a-z)."),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _("Sua senha deve conter pelo menos uma letra minúscula (a-z).")


class DigitValidator:
    """
    Validate that the password contains at least one digit.
    """
    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                _("A senha deve conter pelo menos um número (0-9)."),
                code='password_no_digit',
            )

    def get_help_text(self):
        return _("Sua senha deve conter pelo menos um número (0-9).")


class SpecialCharacterValidator:
    """
    Validate that the password contains at least one special character.
    """
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            raise ValidationError(
                _("A senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;:',.<>?/)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Sua senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;:',.<>?/).")


class MaximumLengthValidator:
    """
    Validate that the password is not too long (prevents DoS attacks).
    """
    def __init__(self, max_length=128):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _("A senha não pode ter mais de %(max_length)d caracteres.") % {'max_length': self.max_length},
                code='password_too_long',
            )

    def get_help_text(self):
        return _("Sua senha não pode ter mais de %(max_length)d caracteres.") % {'max_length': self.max_length}


class NoSequentialCharactersValidator:
    """
    Validate that the password doesn't contain sequential characters like '123', 'abc', 'aaa'.
    """
    def validate(self, password, user=None):
        # Check for sequential numbers (123, 234, etc.)
        for i in range(len(password) - 2):
            if password[i:i+3].isdigit():
                nums = [int(password[i+j]) for j in range(3)]
                if nums[1] == nums[0] + 1 and nums[2] == nums[1] + 1:
                    raise ValidationError(
                        _("A senha não pode conter sequências numéricas (ex: 123, 456)."),
                        code='password_sequential_numbers',
                    )
        
        # Check for sequential letters (abc, xyz, etc.)
        for i in range(len(password) - 2):
            if password[i:i+3].isalpha():
                chars = [ord(password[i+j].lower()) for j in range(3)]
                if chars[1] == chars[0] + 1 and chars[2] == chars[1] + 1:
                    raise ValidationError(
                        _("A senha não pode conter sequências de letras (ex: abc, xyz)."),
                        code='password_sequential_letters',
                    )
        
        # Check for repeated characters (aaa, 111, etc.)
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                raise ValidationError(
                    _("A senha não pode conter 3 ou mais caracteres repetidos consecutivos (ex: aaa, 111)."),
                    code='password_repeated_chars',
                )

    def get_help_text(self):
        return _("Sua senha não pode conter sequências (123, abc) ou caracteres repetidos (aaa, 111).")


class NoCommonPatternsValidator:
    """
    Validate that the password doesn't contain common patterns.
    """
    def __init__(self):
        self.common_patterns = [
            'senha', 'password', 'admin', 'usuario', 'user',
            'qwerty', 'asdfgh', 'zxcvbn', '123456', 'abcdef',
            'peticao', 'brasil', 'gov.br', 'govbr'
        ]

    def validate(self, password, user=None):
        password_lower = password.lower()
        for pattern in self.common_patterns:
            if pattern in password_lower:
                raise ValidationError(
                    _("A senha não pode conter palavras comuns ou previsíveis."),
                    code='password_common_pattern',
                )

    def get_help_text(self):
        return _("Sua senha não pode conter palavras comuns como 'senha', 'admin', 'qwerty', etc.")
