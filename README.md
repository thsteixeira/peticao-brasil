# Democracia Direta

A platform that empowers Brazilian citizens to create, sign, and manage public petitions for specific political causes using official Gov.br digital signatures.

## Features

- **Petition Creation**: Authenticated users can create petitions with rich text formatting
- **Digital Signatures**: Integration with Brazil's official Gov.br electronic signature system
- **Signature Verification**: Automated validation of signed PDFs
- **Security**: LGPD-compliant data protection, file sanitization, and fraud prevention
- **Transparency**: Public petition counts and signature tracking

## Technology Stack

- **Backend**: Django 5.0, Python 3.11+
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **PDF Generation**: ReportLab
- **File Storage**: AWS S3 (production) / Local (development)
- **Frontend**: TailwindCSS, Alpine.js
- **Deployment**: Heroku

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL (optional for development, can use SQLite)
- Redis (for Celery)
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "DEMOCRACIA DIRETA"
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
copy .env.example .env
# Edit .env with your configuration
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

8. **Run Celery worker** (in another terminal)
```bash
celery -A config worker -l info
```

9. **Run Celery beat** (in another terminal, for scheduled tasks)
```bash
celery -A config beat -l info
```

## Project Structure

```
DEMOCRACIA DIRETA/
├── apps/
│   ├── accounts/       # User authentication and management
│   ├── petitions/      # Petition creation and listing
│   ├── signatures/     # Signature submission and verification
│   └── core/           # Shared utilities and base classes
├── config/
│   ├── settings/       # Django settings (base, development, production)
│   ├── urls.py         # Main URL configuration
│   ├── wsgi.py         # WSGI configuration
│   ├── asgi.py         # ASGI configuration
│   └── celery.py       # Celery configuration
├── DOCS/               # Project documentation
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── media/              # User-uploaded files
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
└── .env                # Environment variables (not in git)
```

## Development Workflow

1. Always activate the virtual environment before working
2. Run migrations after pulling changes: `python manage.py migrate`
3. Keep .env file updated with required variables
4. Run tests before committing: `pytest`
5. Format code with Black: `black .`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps

# Run specific test file
pytest apps/petitions/tests/test_models.py
```

## Deployment

See [DOCS/08-deployment-checklist.md](DOCS/08-deployment-checklist.md) for complete deployment instructions.

## License

[License information to be added]

## Contributors

[Contributors list to be added]
