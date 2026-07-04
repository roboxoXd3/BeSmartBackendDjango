"""
Django settings for besmart_backend project.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS.extend([
    "api.xbesmart.com",
    ".railway.app"
])

# Railway provides RAILWAY_PUBLIC_DOMAIN at runtime — add it automatically
RAILWAY_PUBLIC_DOMAIN = os.getenv('RAILWAY_PUBLIC_DOMAIN')
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

# Also allow .railway.app subdomains for convenience
if '.up.railway.app' not in str(ALLOWED_HOSTS):
    ALLOWED_HOSTS.append('.railway.app')

ALLOWED_HOSTS.append('testserver')
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # PostgreSQL extras
    'django.contrib.postgres',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'channels',
    'storages',
    'django_filters',
    
    # Local apps
    'users',
    'products',
    'orders',
    'payments',
    'loyalty',
    'vendors',
    'admin_api',
    'support',
    'categories',
    'currency',
    'content',
    'search',
    'ai_services',
    
    # Observability
    'django_prometheus',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS first
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'besmart_backend.middleware.tracing_middleware.TracingMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'besmart_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'besmart_backend.wsgi.application'
ASGI_APPLICATION = 'besmart_backend.asgi.application'

# Database configuration
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

if DB_NAME and DB_USER and DB_PASSWORD and DB_HOST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT or '5432',
            'CONN_MAX_AGE': 60,
        }
    }
else:
    # Fallback to sqlite for development if env not set
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Storage Configuration (Cloudflare R2)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'auto')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_BUCKET', 'my-assets')

# Supabase Auth Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')

# Bucket Names
BUCKET_PRODUCTS = os.getenv('BUCKET_PRODUCTS', 'products')
BUCKET_PRODUCT_VIDEOS = os.getenv('BUCKET_PRODUCT_VIDEOS', 'product-videos')
BUCKET_CATEGORIES = os.getenv('BUCKET_CATEGORIES', 'categories')
BUCKET_CATEGORY_IMAGES = os.getenv('BUCKET_CATEGORY_IMAGES', 'category-images')
BUCKET_AVATARS = os.getenv('BUCKET_AVATARS', 'avatars')
BUCKET_ADMIN_PROFILES = os.getenv('BUCKET_ADMIN_PROFILES', 'admin-profiles')
BUCKET_PROMOTIONAL_BANNERS = os.getenv('BUCKET_PROMOTIONAL_BANNERS', 'promotional-banners')
BUCKET_HERO_SECTION = os.getenv('BUCKET_HERO_SECTION', 'hero-section')
BUCKET_DOCUMENTS = os.getenv('BUCKET_DOCUMENTS', 'documents')

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    # Helper to create storage config
    def get_storage_config(location_name):
        return {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "endpoint_url": AWS_S3_ENDPOINT_URL,
                "region_name": AWS_S3_REGION_NAME,
                "custom_domain": AWS_S3_CUSTOM_DOMAIN,
                "location": location_name,
                "querystring_auth": False,
            },
        }

    STORAGES = {
        "default": get_storage_config(''), # Default to root of bucket
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        # Named storages
        "products": get_storage_config(BUCKET_PRODUCTS),
        "product_videos": get_storage_config(BUCKET_PRODUCT_VIDEOS),
        "categories": get_storage_config(BUCKET_CATEGORIES),
        "category_images": get_storage_config(BUCKET_CATEGORY_IMAGES),
        "avatars": get_storage_config(BUCKET_AVATARS),
        "admin_profiles": get_storage_config(BUCKET_ADMIN_PROFILES),
        "banners": get_storage_config(BUCKET_PROMOTIONAL_BANNERS),
        "hero_section": get_storage_config(BUCKET_HERO_SECTION),
        "documents": get_storage_config(BUCKET_DOCUMENTS),
    }

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.SupabaseAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7), 
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Swagger / OpenAPI Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'BeSmart Backend API',
    'DESCRIPTION': 'API for BeSmart Mobile App, Website, Vendor Dashboard, and Admin Panel',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Channel Layer (Redis)
if os.getenv('REDIS_URL'):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.getenv('REDIS_URL')],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
]
if RAILWAY_PUBLIC_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

# CSRF Trusted Origins (required for Railway)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
]
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")
CSRF_TRUSTED_ORIGINS.append("https://*.railway.app")

# Squad Payment Gateway
SQUAD_SECRET_KEY = os.environ.get('SQUAD_PRIVATE_KEY', os.environ.get('SQUAD_SECRET_KEY', ''))
SQUAD_BASE_URL = os.environ.get('SQUAD_BASE_URL', 'https://api-d.squadco.com')

# ---------------------------------------------------------------------
# OBSERVABILITY & LOGGING CONFIGURATION
# ---------------------------------------------------------------------
import structlog
import logging.config

LOKI_URL = os.getenv('LOKI_URL') # e.g., 'http://loki:3100/loki/api/v1/push'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local' if DEBUG else 'production')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'ignore_prometheus': {
            '()': 'besmart_backend.logging_filters.PrometheusEndpointFilter',
        },
    },
    'formatters': {
        'json': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
        },
        'plain': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.ConsoleRenderer(colors=True),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'plain',
            'filters': ['ignore_prometheus'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'besmart_backend': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'products': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'orders': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'payments': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'loyalty': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'vendors': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'admin_api': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'support': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'categories': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'currency': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        # You can add custom loggers here if needed
    },
}

import queue

if LOKI_URL:
    LOGGING['handlers']['loki'] = {
        '()': 'logging_loki.LokiQueueHandler',
        'queue': queue.Queue(-1),
        'url': LOKI_URL,
        'tags': {'app': 'besmart_backend', 'env': ENVIRONMENT},
        'version': '1',
        'formatter': 'json',
        'filters': ['ignore_prometheus'],
    }
    LOGGING['loggers']['django']['handlers'].append('loki')
    LOGGING['loggers']['besmart_backend']['handlers'].append('loki')
    
    # Append Loki handler to all our local apps
    for app in ['users', 'products', 'orders', 'payments', 'loyalty', 'vendors', 'admin_api', 'support', 'categories', 'currency']:
        LOGGING['loggers'][app]['handlers'].append('loki')

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
