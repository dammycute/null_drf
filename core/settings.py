"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 4.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path
from datetime import timedelta
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from decouple import config


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['htcode12.pythonanywhere.com', '127.0.0.1',]
AUTH_USER_MODEL = 'authApp.CustomUser'




# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'proper',
    # 'business',
    'authApp',
    'djoser',
    'rest_framework_simplejwt',
    'drf_yasg',
    # 'django.contrib.staticfiles',
    'cloudinary_storage',
]

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    
    
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        },
    },
    'USE_SESSION_AUTH': False,
    'USE_BASIC_AUTH_WITH_SESSION': False,
}

# AUTHENTICATION_BACKENDS = [
#     'social_core.backends.google.GoogleOAuth2',
#     'social_core.backends.facebook.FacebookOAuth2',
#     # other backends
#     'django.contrib.auth.backends.ModelBackend',
# ]

CLOUDINARY_STORAGE = {
   'CLOUD_NAME': config('CLOUD_NAME'),
   'API_KEY': config('API_KEY'),
   'API_SECRET': config('API_SECRET'),
   'secure': config('Bool')
}





# GQAUL-CLAV9-5J6LV-EQMUE-NFYTP     

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1)
}

# DJOSER = {
#     'LOGIN_FIELD': 'email',
#     'USER_CREATE_PASSWORD_RETYPE': True,
#     'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
#     'SEND_CONFIRMATION_EMAIL': True,
#     'SET_PASSWORD_RETYPE': True,
#     'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
#     'ACTIVATION_URL': 'activate/{uid}/{token}',
#     'SEND_ACTIVATION_EMAIL': True,
#     'SERIALIZERS': {
#         'user_create': 'business.serializers.UserCreateSerializer',
#         'current_user': 'business.serializers.UserSerializer',
#         'user_delete': 'djoser.serializers.UserDeleteSerializer',
#     }
# }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

EMAIL_BACKEND = config('Email_Backend')
EMAIL_HOST = config('Email_Host')
EMAIL_PORT = 587
EMAIL_HOST_USER = config('Host_User')
EMAIL_HOST_PASSWORD = config('Host_Password')
EMAIL_USE_TLS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'password_change_file': {
            'level': 'INFO',  # Set the desired log level (INFO, WARNING, etc.).
            'class': 'logging.FileHandler',
            'filename': 'C:\Desktop\log\change_log.log',  # Replace with your desired log file path.
        },
    },
    'loggers': {
        'password_change_logger': {
            'handlers': ['password_change_file'],
            'level': 'INFO',  # Set the desired log level.
            'propagate': False,
        },
    },
}

PAYSTACK_SECRET_KEY = config('PAY_SECRET_KEY')
PAYSTACK_PUBLIC_KEY = config('PAY_PUBLIC_KEY')

CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_APP = 'authApp'

FLUTTERWAVE_PUBLIC_KEY=config('FLUTTERWAVE_PUBLIC_KEY')
FLUTTERWAVE_SECRET_KEY=config('FLUTTERWAVE_SECURITY_KEY')
SECRET_HASH = config('HASH_CODE')

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'realown',
        'USER': 'postgres',
        'PASSWORD': 'htcode12',  # Use the password you set
        'HOST': 'localhost',  # Use 'localhost' if PostgreSQL is on the same machine
        'PORT': '',  # Leave it empty for the default PostgreSQL port (5432)
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
