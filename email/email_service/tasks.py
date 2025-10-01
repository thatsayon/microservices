from celery import shared_task
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, **kwargs):
    """
    Async email sending with Celery
    
    Args:
        All arguments from EmailService.send_email()
    
    Returns:
        dict: Result of email sending
    """
    # Import here to avoid circular imports
    from .services import EmailService
    
    try:
        logger.info(f"Processing email task to {kwargs.get('to_email')}")
        result = EmailService.send_email(**kwargs)
        logger.info(f"Email task completed: {result}")
        return result
    except Exception as exc:
        logger.error(f"Email task failed: {str(exc)}")
        # Retry after 60 seconds, max 3 times
        raise self.retry(exc=exc, countdown=60)


@shared_task
def retry_failed_emails():
    """
    Retry failed emails (runs every 5 minutes via Celery Beat)
    
    This task automatically retries failed emails that:
    - Failed in the last 24 hours
    - Have been retried less than 3 times
    """
    # Import here to avoid circular imports
    from .models import EmailLog, EmailStatus
    
    # Get failed emails from last 24 hours with retry_count < 3
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    
    failed_emails = EmailLog.objects.filter(
        status=EmailStatus.FAILED,
        retry_count__lt=3,
        created_at__gte=twenty_four_hours_ago
    )
    
    logger.info(f"Found {failed_emails.count()} failed emails to retry")
    
    retried_count = 0
    for email_log in failed_emails:
        try:
            # Retry sending
            send_email_task.delay(
                to_email=email_log.to_email,
                to_name=email_log.to_name,
                subject=email_log.subject,
                body_html=email_log.body_html,
                body_text=email_log.body_text,
                template_name=email_log.template_name,
                template_data=email_log.template_data,
                cc=email_log.cc,
                bcc=email_log.bcc,
                service_name=email_log.service_name,
                user_id=email_log.user_id
            )
            logger.info(f"Retrying email {email_log.id}")
            retried_count += 1
        except Exception as e:
            logger.error(f"Failed to queue retry for email {email_log.id}: {str(e)}")
    
    return {
        "retried_count": retried_count,
        "total_failed": failed_emails.count()
    }


@shared_task
def cleanup_old_emails():
    """
    Clean up old email logs (runs daily via Celery Beat)
    
    Deletes email logs older than 90 days
    """
    # Import here to avoid circular imports
    from .models import EmailLog
    
    ninety_days_ago = datetime.now() - timedelta(days=90)
    
    old_emails = EmailLog.objects.filter(created_at__lt=ninety_days_ago)
    count = old_emails.count()
    
    old_emails.delete()
    
    logger.info(f"Cleaned up {count} old email logs")
    
    return {
        "deleted_count": count
    }
