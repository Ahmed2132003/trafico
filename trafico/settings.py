from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-qwohvnnk!!+(h09z*u7vnandq62mfl#39hvv4vi+f8jgiiaa!i'
DEBUG = True
ALLOWED_HOSTS = []
APPEND_SLASH = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users.apps.UsersConfig',
    'products.apps.ProductsConfig',
    'orders.apps.OrdersConfig',
    'crispy_forms',
    'dashboard.apps.DashboardConfig',
]

AUTH_USER_MODEL = 'users.User'
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = 'dashboard:dashboard'
CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trafico.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'trafico.wsgi.application'



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

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('ar', 'Arabic'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# إعدادات البريد الإلكتروني
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'trafico.tt12@gmail.com'
EMAIL_HOST_PASSWORD = 'lpjj tkow dano sdes'

import os
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:////data/db.sqlite3",
        conn_max_age=600
    )
}

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] 
STATIC_ROOT = BASE_DIR / 'staticfiles'  
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'  
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "trafico.fly.dev"]
CSRF_TRUSTED_ORIGINS = ["https://trafico.fly.dev"]

#DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
DEBUG = True