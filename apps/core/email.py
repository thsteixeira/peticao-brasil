"""
Email utilities for Petição Brasil.
Handles email template rendering and sending.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_template_email(
    subject,
    template_name,
    context,
    recipient_list,
    from_email=None,
    fail_silently=False
):
    """
    Send an email using an HTML template.
    
    Args:
        subject: Email subject
        template_name: Path to template (without .html extension)
        context: Template context dictionary
        recipient_list: List of recipient email addresses
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        fail_silently: Whether to suppress exceptions
        
    Returns:
        Number of successfully sent emails
    """
    if not recipient_list:
        logger.warning(f'No recipients for email: {subject}')
        return 0
    
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # Add site name to context
        context['site_name'] = settings.SITE_NAME
        context['site_url'] = settings.SITE_URL
        
        # Render HTML template
        html_content = render_to_string(f'emails/{template_name}.html', context)
        
        # Create plain text version by stripping HTML tags
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        result = email.send(fail_silently=fail_silently)
        
        if result:
            logger.info(f'Email sent: {subject} to {", ".join(recipient_list)}')
        else:
            logger.warning(f'Email not sent: {subject}')
            
        return result
        
    except Exception as e:
        logger.error(f'Error sending email "{subject}": {str(e)}')
        if not fail_silently:
            raise
        return 0


def send_signature_verified_email(signature):
    """
    Send notification when signature is verified, including custody certificate link.
    """
    if not signature.email:
        return 0
        
    context = {
        'signature': signature,
        'petition': signature.petition,
        'signer_name': signature.full_name,
        'site_url': settings.SITE_URL,
    }
    
    return send_template_email(
        subject=f'Assinatura Verificada - {signature.petition.title}',
        template_name='signature_verified_with_certificate',
        context=context,
        recipient_list=[signature.email]
    )


def send_signature_rejected_email(signature):
    """
    Send notification when signature is rejected.
    """
    if not signature.email:
        return 0
        
    context = {
        'signature': signature,
        'petition': signature.petition,
        'signer_name': signature.full_name,
        'reason': signature.rejection_reason,
    }
    
    return send_template_email(
        subject=f'Assinatura Rejeitada - {signature.petition.title}',
        template_name='signature_rejected',
        context=context,
        recipient_list=[signature.email]
    )


def send_petition_milestone_email(petition, milestone_percentage):
    """
    Send notification to petition creator when milestone is reached.
    """
    if not petition.created_by or not petition.created_by.email:
        return 0
    
    context = {
        'petition': petition,
        'milestone': milestone_percentage,
        'current_signatures': petition.current_signatures,
        'signature_goal': petition.signature_goal,
    }
    
    return send_template_email(
        subject=f'Meta de {milestone_percentage}% Alcançada - {petition.title}',
        template_name='petition_milestone',
        context=context,
        recipient_list=[petition.created_by.email]
    )


def send_petition_created_success_email(petition):
    """
    Send notification to petition creator when petition is successfully created
    and PDF is generated.
    """
    if not petition.creator or not petition.creator.email:
        return 0
    
    context = {
        'petition': petition,
        'creator_name': petition.creator.get_full_name() or petition.creator.username,
        'petition_url': petition.get_absolute_url(),
    }
    
    return send_template_email(
        subject=f'Petição Criada com Sucesso - {petition.title}',
        template_name='petition_created_success',
        context=context,
        recipient_list=[petition.creator.email]
    )


def send_petition_created_failure_email(petition):
    """
    Send notification to petition creator when petition is created
    but PDF generation failed.
    """
    if not petition.creator or not petition.creator.email:
        return 0
    
    context = {
        'petition': petition,
        'creator_name': petition.creator.get_full_name() or petition.creator.username,
        'petition_url': petition.get_absolute_url(),
    }
    
    return send_template_email(
        subject=f'Petição Criada - Problema na Geração do PDF - {petition.title}',
        template_name='petition_created_failure',
        context=context,
        recipient_list=[petition.creator.email]
    )
