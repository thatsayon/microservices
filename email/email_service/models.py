from django.db import models
import uuid

class EmailStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'
    BOUNCED = 'bounced', 'Bounced'
    DELIVERED = 'delivered', 'Delivered'
    OPENED = 'opened', 'Opened'
    CLICKED = 'clicked', 'Clicked'

class EmailLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient info
    to_email = models.EmailField()
    to_name = models.CharField(max_length=255, blank=True, null=True)
    cc = models.JSONField(blank=True, null=True)
    bcc = models.JSONField(blank=True, null=True)
    
    # Email content
    subject = models.CharField(max_length=500)
    body_html = models.TextField(blank=True, null=True)
    body_text = models.TextField(blank=True, null=True)
    
    # Template info
    template_name = models.CharField(max_length=100, blank=True, null=True)
    template_data = models.JSONField(blank=True, null=True)
    
    # Metadata
    service_name = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Provider info
    provider = models.CharField(max_length=50)
    provider_message_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.QUEUED
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'email_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_email']),
            models.Index(fields=['status']),
            models.Index(fields=['service_name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.to_email} - {self.subject} - {self.status}"

class EmailTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=500)
    html_content = models.TextField()
    text_content = models.TextField(blank=True, null=True)
    
    # Metadata
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['name']
    
    def __str__(self):
        return self.name

