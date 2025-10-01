from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import EmailLog, EmailStatus, EmailTemplate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body_html: str = None,
        body_text: str = None,
        template_name: str = None,
        template_data: dict = None,
        cc: list = None,
        bcc: list = None,
        service_name: str = "unknown",
        user_id: str = None,
        to_name: str = None
    ):
        """Send email using configured provider"""
        
        # Render template if provided
        if template_name:
            if template_data is None:
                template_data = {}
            try:
                # Try to get from database first
                try:
                    template_obj = EmailTemplate.objects.get(name=template_name, is_active=True)
                    body_html = template_obj.html_content
                    body_text = template_obj.text_content
                    
                    # Replace variables in template
                    for key, value in template_data.items():
                        body_html = body_html.replace(f"{{{{ {key} }}}}", str(value))
                        if body_text:
                            body_text = body_text.replace(f"{{{{ {key} }}}}", str(value))
                    
                    if not subject and template_obj.subject:
                        subject = template_obj.subject
                        for key, value in template_data.items():
                            subject = subject.replace(f"{{{{ {key} }}}}", str(value))
                            
                except EmailTemplate.DoesNotExist:
                    # Fall back to file template
                    body_html = render_to_string(f'emails/{template_name}.html', template_data)
                    
            except Exception as e:
                logger.error(f"Template rendering failed: {str(e)}")
                raise
        
        # Create email log
        email_log = EmailLog.objects.create(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            template_name=template_name,
            template_data=template_data,
            cc=cc,
            bcc=bcc,
            service_name=service_name,
            user_id=user_id,
            provider=settings.EMAIL_PROVIDER,
            status=EmailStatus.QUEUED
        )
        
        try:
            # Route to appropriate provider
            provider = settings.EMAIL_PROVIDER.lower()
            
            if provider == 'sendgrid':
                message_id = EmailService._send_sendgrid(
                    to_email, subject, body_html, body_text, cc, bcc, to_name
                )
            elif provider == 'ses':
                message_id = EmailService._send_ses(
                    to_email, subject, body_html, body_text, cc, bcc, to_name
                )
            elif provider == 'smtp':
                message_id = EmailService._send_smtp(
                    to_email, subject, body_html, body_text, cc, bcc, to_name
                )
            else:
                raise ValueError(f"Unsupported email provider: {provider}")
            
            # Update log
            email_log.status = EmailStatus.SENT
            email_log.sent_at = datetime.now()
            email_log.provider_message_id = message_id
            email_log.save()
            
            logger.info(f"Email sent successfully to {to_email} via {provider}")
            
            return {
                "success": True,
                "email_id": str(email_log.id),
                "message_id": message_id
            }
            
        except Exception as e:
            email_log.status = EmailStatus.FAILED
            email_log.failed_at = datetime.now()
            email_log.error_message = str(e)
            email_log.retry_count += 1
            email_log.save()
            
            logger.error(f"Email send failed to {to_email}: {str(e)}")
            raise e
    
    @staticmethod
    def _send_smtp(to_email, subject, body_html, body_text, cc, bcc, to_name):
        """Send via SMTP (Django default)"""
        from_email = f"{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>"
        to = [f"{to_name} <{to_email}>" if to_name else to_email]
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=body_text or "Please view this email in HTML format.",
            from_email=from_email,
            to=to,
            cc=cc,
            bcc=bcc
        )
        
        if body_html:
            email.attach_alternative(body_html, "text/html")
        
        email.send()
        return f"smtp-{to_email}-{datetime.now().timestamp()}"
    
    @staticmethod
    def _send_sendgrid(to_email, subject, body_html, body_text, cc, bcc, to_name):
        """Send via SendGrid API"""
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content, Cc, Bcc
        
        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        
        from_email = Email(settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_NAME)
        to_email_obj = To(to_email, to_name)
        
        # Create mail object
        mail = Mail(
            from_email=from_email,
            to_emails=to_email_obj,
            subject=subject
        )
        
        # Add content
        if body_text:
            mail.add_content(Content("text/plain", body_text))
        if body_html:
            mail.add_content(Content("text/html", body_html))
        
        # Add CC
        if cc:
            for cc_email in cc:
                mail.add_cc(Cc(cc_email))
        
        # Add BCC
        if bcc:
            for bcc_email in bcc:
                mail.add_bcc(Bcc(bcc_email))
        
        # Send
        response = sg.send(mail)
        
        if response.status_code not in [200, 202]:
            raise Exception(f"SendGrid error: {response.body}")
        
        # Extract message ID from headers
        message_id = response.headers.get('X-Message-Id', f"sendgrid-{datetime.now().timestamp()}")
        
        return message_id
    
    @staticmethod
    def _send_ses(to_email, subject, body_html, body_text, cc, bcc, to_name):
        """Send via AWS SES"""
        import boto3
        from botocore.exceptions import ClientError
        
        # Create SES client
        ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Prepare destination
        destination = {
            'ToAddresses': [to_email]
        }
        
        if cc:
            destination['CcAddresses'] = cc
        if bcc:
            destination['BccAddresses'] = bcc
        
        # Prepare message
        message = {
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            }
        }
        
        # Add body
        body = {}
        if body_text:
            body['Text'] = {
                'Data': body_text,
                'Charset': 'UTF-8'
            }
        if body_html:
            body['Html'] = {
                'Data': body_html,
                'Charset': 'UTF-8'
            }
        
        message['Body'] = body
        
        # Send email
        try:
            response = ses_client.send_email(
                Source=f"{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>",
                Destination=destination,
                Message=message
            )
            
            return response['MessageId']
            
        except ClientError as e:
            logger.error(f"SES error: {e.response['Error']['Message']}")
            raise Exception(f"SES error: {e.response['Error']['Message']}")

