"""
Test email sending functionality.
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import smtplib


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        
        self.stdout.write(self.style.WARNING(f'Testing email configuration...'))
        self.stdout.write(f'SMTP Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'SMTP Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'Use TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'Username: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'From Email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Recipient: {recipient}')
        self.stdout.write('')
        
        # Test SMTP connection first
        self.stdout.write('Testing SMTP connection...')
        try:
            if settings.EMAIL_USE_SSL:
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
            elif settings.EMAIL_USE_TLS:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            self.stdout.write(self.style.SUCCESS('✅ SMTP connection successful!'))
            server.quit()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ SMTP connection failed: {str(e)}'))
            self.stdout.write('')
            self.stdout.write('Common fixes:')
            self.stdout.write('1. Check if EMAIL_HOST is correct (try smtp.uol.com.br or smtps.uol.com.br)')
            self.stdout.write('2. Try port 465 with SSL instead of 587 with TLS')
            self.stdout.write('3. Verify username and password are correct')
            self.stdout.write('4. Check if firewall is blocking SMTP')
            return
        
        # Now try sending email
        self.stdout.write('')
        self.stdout.write(f'Sending test email to {recipient}...')
        
        try:
            send_mail(
                subject='Teste - Petição Brasil',
                message='Este é um email de teste do sistema Petição Brasil.\n\nSe você recebeu esta mensagem, a configuração de email está funcionando corretamente!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Email enviado com sucesso para {recipient}!'))
            self.stdout.write('Check your inbox (and spam folder)')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao enviar email: {str(e)}'))
            raise
