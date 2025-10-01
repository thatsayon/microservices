from rest_framework import serializers
from .models import EmailLog, EmailTemplate

class SendEmailSerializer(serializers.Serializer):
    """Serializer for sending emails"""
    to_email = serializers.EmailField()
    to_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    subject = serializers.CharField(max_length=500)
    body_html = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    body_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    template_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    template_data = serializers.JSONField(required=False, allow_null=True, default=dict)
    cc = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_null=True,
        allow_empty=True
    )
    bcc = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_null=True,
        allow_empty=True
    )
    service_name = serializers.CharField(max_length=100)
    user_id = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    send_async = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validate that either body content or template is provided"""
        has_body = data.get('body_html') or data.get('body_text')
        has_template = data.get('template_name')
        
        if not has_body and not has_template:
            raise serializers.ValidationError(
                "Must provide either body_html/body_text or template_name"
            )
        
        return data


class EmailLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailLog model"""
    
    class Meta:
        model = EmailLog
        fields = [
            'id',
            'to_email',
            'to_name',
            'cc',
            'bcc',
            'subject',
            'body_html',
            'body_text',
            'template_name',
            'template_data',
            'service_name',
            'user_id',
            'provider',
            'provider_message_id',
            'status',
            'created_at',
            'updated_at',
            'sent_at',
            'failed_at',
            'error_message',
            'retry_count'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'sent_at',
            'failed_at',
            'provider_message_id'
        ]


class EmailLogListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing emails (without body content)"""
    
    class Meta:
        model = EmailLog
        fields = [
            'id',
            'to_email',
            'to_name',
            'subject',
            'service_name',
            'user_id',
            'provider',
            'status',
            'created_at',
            'sent_at',
            'error_message'
        ]
        read_only_fields = fields


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate model"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id',
            'name',
            'subject',
            'html_content',
            'text_content',
            'description',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Ensure template name is unique (case-insensitive)"""
        if self.instance:
            # Update case - exclude current instance
            if EmailTemplate.objects.exclude(id=self.instance.id).filter(name__iexact=value).exists():
                raise serializers.ValidationError("A template with this name already exists")
        else:
            # Create case
            if EmailTemplate.objects.filter(name__iexact=value).exists():
                raise serializers.ValidationError("A template with this name already exists")
        return value


class EmailTemplateListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing templates (without content)"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id',
            'name',
            'subject',
            'description',
            'is_active',
            'created_at'
        ]
        read_only_fields = fields

