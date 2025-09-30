# ============================================
# core/settings.py (UPDATED)
# ============================================
from pathlib import Path
import environ
import os

env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='*').split(',')

# Application definition - REMOVED AUTH APPS
INSTALLED_APPS = [
    # Minimal Django apps (NO admin, NO auth, NO sessions)
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
]

# Local apps
INSTALLED_APPS += [
    'email_service'
]

# Third-party apps
INSTALLED_APPS += [
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
]

# REMOVED auth-related middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'email_service.middleware.InternalAPIKeyMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASS'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT')
    }
}

# REST Framework - No Authentication
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# CORS
CORS_ALLOW_ALL_ORIGINS = env('CORS_ALLOW_ALL', default=True)
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS', default='').split(',') if env('CORS_ALLOWED_ORIGINS', default='') else []

# ============================================
# EMAIL CONFIGURATION (UPDATED)
# ============================================
EMAIL_PROVIDER = env('EMAIL_PROVIDER', default='smtp').lower()

# Common Email Settings
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')
DEFAULT_FROM_NAME = env('DEFAULT_FROM_NAME', default='My Platform')

# SMTP Configuration
if EMAIL_PROVIDER == 'smtp':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = env('EMAIL_PORT', default=587)
    EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# SendGrid Configuration
elif EMAIL_PROVIDER == 'sendgrid':
    SENDGRID_API_KEY = env('SENDGRID_API_KEY')
    if not SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY must be set when using SendGrid provider")

# AWS SES Configuration
elif EMAIL_PROVIDER == 'ses':
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_SES_REGION = env('AWS_SES_REGION', default='us-east-1')
    
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS credentials must be set when using SES provider")

else:
    raise ValueError(f"Invalid EMAIL_PROVIDER: {EMAIL_PROVIDER}. Must be 'smtp', 'sendgrid', or 'ses'")

# ============================================
# CELERY CONFIGURATION
# ============================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Celery Beat Schedule (for retry failed emails)
CELERY_BEAT_SCHEDULE = {
    'retry-failed-emails': {
        'task': 'email_service.tasks.retry_failed_emails',
        'schedule': 300.0,  # Every 5 minutes
    },
}

# ============================================
# INTERNAL API SECURITY
# ============================================
INTERNAL_API_KEY = env('INTERNAL_API_KEY')
ALLOWED_SERVICES = env('ALLOWED_SERVICES', default='auth-service,project-service').split(',')

# Rate Limiting
RATE_LIMIT_PER_HOUR = env('RATE_LIMIT_PER_HOUR', default=100)

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# LOGGING
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'email_service.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'email_service': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
