"""
Tests for custom password validators.
"""
import pytest
from django.core.exceptions import ValidationError
from apps.core.password_validators import (
    UppercaseValidator,
    LowercaseValidator,
    DigitValidator,
    SpecialCharacterValidator,
    MaximumLengthValidator,
    NoSequentialCharactersValidator,
    NoCommonPatternsValidator,
)


class TestUppercaseValidator:
    """Test uppercase letter validator"""
    
    def test_valid_password_with_uppercase(self):
        """Password with uppercase should pass"""
        validator = UppercaseValidator()
        try:
            validator.validate('Password123!')
        except ValidationError:
            pytest.fail("Valid password was rejected")
    
    def test_invalid_password_without_uppercase(self):
        """Password without uppercase should fail"""
        validator = UppercaseValidator()
        with pytest.raises(ValidationError):
            validator.validate('password123!')


class TestLowercaseValidator:
    """Test lowercase letter validator"""
    
    def test_valid_password_with_lowercase(self):
        """Password with lowercase should pass"""
        validator = LowercaseValidator()
        try:
            validator.validate('Password123!')
        except ValidationError:
            pytest.fail("Valid password was rejected")
    
    def test_invalid_password_without_lowercase(self):
        """Password without lowercase should fail"""
        validator = LowercaseValidator()
        with pytest.raises(ValidationError):
            validator.validate('PASSWORD123!')


class TestDigitValidator:
    """Test digit validator"""
    
    def test_valid_password_with_digit(self):
        """Password with digit should pass"""
        validator = DigitValidator()
        try:
            validator.validate('Password123!')
        except ValidationError:
            pytest.fail("Valid password was rejected")
    
    def test_invalid_password_without_digit(self):
        """Password without digit should fail"""
        validator = DigitValidator()
        with pytest.raises(ValidationError):
            validator.validate('Password!')


class TestSpecialCharacterValidator:
    """Test special character validator"""
    
    def test_valid_password_with_special_char(self):
        """Password with special character should pass"""
        validator = SpecialCharacterValidator()
        try:
            validator.validate('Password123!')
        except ValidationError:
            pytest.fail("Valid password was rejected")
    
    def test_invalid_password_without_special_char(self):
        """Password without special character should fail"""
        validator = SpecialCharacterValidator()
        with pytest.raises(ValidationError):
            validator.validate('Password123')


class TestMaximumLengthValidator:
    """Test maximum length validator"""
    
    def test_valid_password_within_limit(self):
        """Password within length limit should pass"""
        validator = MaximumLengthValidator(max_length=128)
        try:
            validator.validate('Password123!' * 5)  # 60 characters
        except ValidationError:
            pytest.fail("Valid password was rejected")
    
    def test_invalid_password_too_long(self):
        """Password exceeding length limit should fail"""
        validator = MaximumLengthValidator(max_length=20)
        with pytest.raises(ValidationError):
            validator.validate('Password123!Password123!')  # 24 characters


class TestNoSequentialCharactersValidator:
    """Test sequential characters validator"""
    
    def test_valid_password_no_sequences(self):
        """Password without sequences should pass"""
        validator = NoSequentialCharactersValidator()
        try:
            validator.validate('P@ssw0rd2024!')
        except ValidationError:
            pytest.fail("Valid password was rejected")
    
    def test_invalid_password_with_number_sequence(self):
        """Password with number sequence should fail"""
        validator = NoSequentialCharactersValidator()
        with pytest.raises(ValidationError):
            validator.validate('Password123!')
    
    def test_invalid_password_with_letter_sequence(self):
        """Password with letter sequence should fail"""
        validator = NoSequentialCharactersValidator()
        with pytest.raises(ValidationError):
            validator.validate('Pabc123!')
    
    def test_invalid_password_with_repeated_chars(self):
        """Password with repeated characters should fail"""
        validator = NoSequentialCharactersValidator()
        with pytest.raises(ValidationError):
            validator.validate('Paaassword1!')


class TestNoCommonPatternsValidator:
    """Test common patterns validator"""
    
    def test_valid_password_no_common_patterns(self):
        """Password without common patterns should pass"""
        validator = NoCommonPatternsValidator()
        try:
            validator.validate('M3uP@ssw0rd!')
        except ValidationError:
            pytest.fail("Valid password was rejected")
    
    def test_invalid_password_with_senha(self):
        """Password containing 'senha' should fail"""
        validator = NoCommonPatternsValidator()
        with pytest.raises(ValidationError):
            validator.validate('Senha123!')
    
    def test_invalid_password_with_admin(self):
        """Password containing 'admin' should fail"""
        validator = NoCommonPatternsValidator()
        with pytest.raises(ValidationError):
            validator.validate('Admin123!')
    
    def test_invalid_password_with_qwerty(self):
        """Password containing 'qwerty' should fail"""
        validator = NoCommonPatternsValidator()
        with pytest.raises(ValidationError):
            validator.validate('Qwerty123!')


class TestPasswordValidatorIntegration:
    """Test all validators together"""
    
    def test_strong_password_passes_all_validators(self):
        """A strong password should pass all validators"""
        validators = [
            UppercaseValidator(),
            LowercaseValidator(),
            DigitValidator(),
            SpecialCharacterValidator(),
            MaximumLengthValidator(),
            NoSequentialCharactersValidator(),
            NoCommonPatternsValidator(),
        ]
        
        strong_passwords = [
            'M3uP@ssw0rd!',
            'S3cur3P@ssw0rd',
            'C0mpl3x!P@ss',
            'Str0ng#P@ssw0rd',
        ]
        
        for password in strong_passwords:
            for validator in validators:
                try:
                    validator.validate(password)
                except ValidationError as e:
                    pytest.fail(f"Strong password '{password}' failed {validator.__class__.__name__}: {e}")
    
    def test_weak_passwords_fail(self):
        """Weak passwords should fail at least one validator"""
        validators = [
            UppercaseValidator(),
            LowercaseValidator(),
            DigitValidator(),
            SpecialCharacterValidator(),
            NoSequentialCharactersValidator(),
            NoCommonPatternsValidator(),
        ]
        
        weak_passwords = [
            'password',  # No uppercase, digit, special char
            'PASSWORD',  # No lowercase, digit, special char
            'Password',  # No digit, special char
            'Password1',  # No special char
            'password123',  # No uppercase, special char
            'Senha123!',  # Common pattern
            'Admin123!',  # Common pattern
            'Password123!',  # Sequential numbers
        ]
        
        for password in weak_passwords:
            failed = False
            for validator in validators:
                try:
                    validator.validate(password)
                except ValidationError:
                    failed = True
                    break
            
            assert failed, f"Weak password '{password}' should have failed at least one validator"
