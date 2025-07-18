"""
Django settings for pscweb2 project.

Updated for Django 5.x, Python 3.13, and modern deployment practices.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/
"""

import os
from pathlib import Path
import dj_database_url

# Use python-dotenv to load .env file in development
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
# The `DEBUG` variable is expected to be a boolean.
# os.environ.get() returns a string, so we compare it to 'True'.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Get SECRET_KEY from environment variables.
# In development, this can be in the .env file.
SECRET_KEY = os.environ.get('SECRET_KEY')

# If SECRET_KEY is not set (e.g., in development), Django will raise an error.
# This check prevents the app from starting without a key.
if not SECRET_KEY and DEBUG:
    # This is a fallback for local development only.
    # A real key should be in your .env file.
    print("Warning: SECRET_KEY not found in .env. Using a temporary, insecure key.")
    SECRET_KEY = 'temporary-insecure-key-for-development-only'
elif not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for production environment")

ALLOWED_HOSTS = []

# If in production, add the production hostname to ALLOWED_HOSTS.
# Example for Azure:
AZURE_HOSTNAME = os.environ.get('AZURE_HOSTNAME')
if AZURE_HOSTNAME:
    ALLOWED_HOSTS.append(AZURE_HOSTNAME)

# Example for Render (if you use it in the future)
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Your apps
    'accounts.apps.AccountsConfig',
    'production.apps.ProductionConfig',
    'rehearsal.apps.RehearsalConfig',
    'script.apps.ScriptConfig',
    # Third-party apps
    # 'social_django', # Not used, so commented out to prevent ModuleNotFoundError
]

# Recommended for Django 3.2+
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise middleware for serving static files
    # Should be placed right after the SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pscweb2.urls'
LOGIN_REDIRECT_URL = '/'

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
                # 'social_django.context_processors.backends',      # Not used
                # 'social_django.context_processors.login_redirect', # Not used
            ],
        },
    },
]

WSGI_APPLICATION = 'pscweb2.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

if DEBUG:
    # Local development database (PostgreSQL)
    # Reads connection details from your .env file.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'pscweb2'),
            'USER': os.environ.get('DB_USER', 'pscweb2_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    # Production database configured via DATABASE_URL
    # dj_database_url will parse the URL and configure the database.
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            # ssl_require=True # For Azure SQL, SSL is handled by the ODBC driver connection string
        )
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
# USE_L10N was deprecated in Django 4.0 and removed in 5.0.
# USE_I18N = True handles locale-dependent formatting.
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Modern storage backend settings (Django 4.2+)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# For social-auth-app-django (All related settings are commented out)
# SOCIAL_AUTH_URL_NAMESPACE = 'social'
# AUTHENTICATION_BACKENDS = [
#     'social_core.backends.twitter.TwitterOAuth',
#     'django.contrib.auth.backends.ModelBackend',
# ]
# SOCIAL_AUTH_TWITTER_KEY = os.environ.get('SOCIAL_AUTH_TWITTER_KEY')
# SOCIAL_AUTH_TWITTER_SECRET = os.environ.get('SOCIAL_AUTH_TWITTER_SECRET')

# Security settings for production
if not DEBUG:
    # Add your production host to CSRF_TRUSTED_ORIGINS
    if AZURE_HOSTNAME:
        CSRF_TRUSTED_ORIGINS = [f'https://{AZURE_HOSTNAME}']

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
