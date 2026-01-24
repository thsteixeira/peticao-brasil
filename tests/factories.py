"""Factory classes for creating test data"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth import get_user_model
from apps.core.models import Category
from apps.petitions.models import Petition
from apps.signatures.models import Signature

User = get_user_model()
fake = Faker('pt_BR')


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name', locale='pt_BR')
    last_name = factory.Faker('last_name', locale='pt_BR')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('slug',)
    
    name = factory.Sequence(lambda n: f'Categoria {n}')
    slug = factory.Sequence(lambda n: f'categoria-{n}')
    description = factory.Faker('sentence', locale='pt_BR')
    icon = factory.Iterator(['🏥', '📚', '🚌', '🚨'])
    color = factory.Iterator(['#28a745', '#007bff', '#ffc107', '#dc3545'])
    active = True
    order = factory.Sequence(lambda n: n)


class PetitionFactory(DjangoModelFactory):
    class Meta:
        model = Petition
    
    creator = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    title = factory.Faker('sentence', nb_words=6, locale='pt_BR')
    description = factory.Faker('paragraph', nb_sentences=5, locale='pt_BR')
    signature_goal = factory.Iterator([100, 500, 1000, 5000])
    status = Petition.STATUS_ACTIVE
    is_active = True


class SignatureFactory(DjangoModelFactory):
    class Meta:
        model = Signature
    
    petition = factory.SubFactory(PetitionFactory)
    full_name = factory.Faker('name', locale='pt_BR')
    cpf_hash = factory.LazyFunction(lambda: Signature.hash_cpf(fake.cpf()))
    email = factory.Faker('email', locale='pt_BR')
    city = factory.Faker('city', locale='pt_BR')
    state = factory.Iterator(['SP', 'RJ', 'MG', 'BA', 'RS', 'PR'])
    verification_status = Signature.STATUS_PENDING
