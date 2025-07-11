"""
Django settings for solana_steuer_tool project.

Generated by 'django-admin startproject' using Django 4.2.23.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os # Hinzugefügt

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# In einer echten Produktionsumgebung sollte dieser Wert aus einer Umgebungsvariable geladen werden.
# Beispiel: SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'ein_starker_default_key_fuer_entwicklung')
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', "django-insecure-eng00_xz9l3#afzqycpoffno9^ro@c&xs0c@*3w^^od-su%!=s") # Für Demo-Zwecke ggf. alten Wert als Fallback lassen, aber in Produktion UNBEDINGT ändern und sichern!

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG wird standardmäßig auf False gesetzt, es sei denn DJANGO_DEBUG=True ist in den Umgebungsvariablen gesetzt.
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS muss in Produktion auf die tatsächlichen Hosts/Domains der Anwendung gesetzt werden.
# Für einfaches initiales Deployment kann '*' verwendet werden, ist aber unsicher für echte Produktion.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',') if os.environ.get('DJANGO_ALLOWED_HOSTS') else ['*']


# Application definition

INSTALLED_APPS = [
    'wallet_manager.apps.WalletManagerConfig', # Hinzugefügte App
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # Whitenoise Middleware hinzugefügt
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "solana_steuer_tool.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "solana_steuer_tool.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'solana_steuer_db', # Ersetze dies mit deinem Datenbanknamen
        'USER': 'dein_db_benutzer',   # Ersetze dies mit deinem DB-Benutzer
        'PASSWORD': 'dein_db_passwort', # Ersetze dies mit deinem DB-Passwort
        'HOST': 'localhost',             # Oder die IP/Hostname deines DB-Servers
        'PORT': '3306',                  # Standard MySQL/MariaDB Port
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'de-de' # Geändert auf Deutsch

TIME_ZONE = 'UTC' # Beibehaltung von UTC ist oft gut für Serveranwendungen

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# STATIC_ROOT ist das Verzeichnis, in das `collectstatic` alle statischen Dateien für die Produktion kopiert.
STATIC_ROOT = BASE_DIR / "staticfiles"

# Konfiguration für Whitenoise, um auch komprimierte Dateien (Brotli, falls verfügbar) auszuliefern
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
