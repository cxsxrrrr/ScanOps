"""
Django settings for Auditoría Web Automatizada para PYMES.
"""
import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security ---
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# --- Application Definition ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'django_filters',

    # Local apps
    'accounts',
    'urls_manager',
    'scanner',
    'reports',
    'notifications',
    'administration',
    'audit_log',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit_log.middleware.APIRequestLogMiddleware',
]

ROOT_URLCONF = 'auditoria.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'auditoria.wsgi.application'

# --- Database ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='auditoria_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# --- Auth ---
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# --- Static Files ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- Default Primary Key ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Django REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.ClerkJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Keep query param "format" available for app logic (report export format)
    # instead of DRF renderer selection.
    'URL_FORMAT_OVERRIDE': None,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Vigia API',
    'DESCRIPTION': 'Documentacion automatica del backend Vigia.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# --- CORS ---
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')
CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
]
CORS_ALLOW_CREDENTIALS = True

# --- Clerk Auth ---
CLERK_SECRET_KEY = config('CLERK_SECRET_KEY', default='')
CLERK_PUBLISHABLE_KEY = config('CLERK_PUBLISHABLE_KEY', default='')
CLERK_JWKS_URL = config('CLERK_JWKS_URL', default='')
CLERK_ISSUER = config('CLERK_ISSUER', default='')

# --- Celery ---
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
# Run tasks synchronously in dev (no Redis needed). Set False in production.
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config('CELERY_TASK_EAGER_PROPAGATES', default=True, cast=bool)
CELERY_BEAT_SCHEDULE = {
    'send-scheduled-reports': {
        'task': 'notifications.tasks.send_scheduled_reports',
        'schedule': 3600.0,  # Check every hour
    },
}

# --- Google Gemini ---
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# --- Resend ---
RESEND_API_KEY = config('RESEND_API_KEY', default='')
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default='Vigia <onboarding@resend.dev>')

# --- Stripe ---
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# --- Scan Engine Config ---
SCAN_TIMEOUT = 30  # seconds per check
SCAN_MAX_CONCURRENT = 3
SCAN_DEFAULT_DEPTH = 1

# --- Logging ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'auditoria.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'scanner': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
