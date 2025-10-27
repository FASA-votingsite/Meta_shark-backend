# settings_production.py
"""
Production settings for MetaShark Services - HostAfrica deployment
"""

from .settings import *
import os
from decouple import config

# Security settings
DEBUG = False
SECRET_KEY = config('SECRET_KEY')  # Must be set in production

# Allowed hosts for production
ALLOWED_HOSTS = [
    'metasharkservices.com',
    'www.metasharkservices.com',
    '102.89.69.74',  # Add your HostAfrica server IP when you get it
]

# Database configuration for HostAfrica MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('metashar_META_SHARK_ADMIN'),
        'USER': config('META_CEO'),
        'PASSWORD': config('META@ADMIN001'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
}

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://metasharkservices.com",
    "https://www.metasharkservices.com",
]

CORS_ALLOW_ALL_ORIGINS = False

# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = [
    "https://metasharkservices.com",
    "https://www.metasharkservices.com",
]

# Static files - ensure correct paths for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# SSL/HTTPS settings (enable when you have SSL certificate)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

print("Loading production settings for HostAfrica...")