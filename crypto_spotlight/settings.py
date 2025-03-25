import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = []

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = ["crypto", "news", "posts", "contacts"]

THIRD_PARTY_APPS = [
    "django.contrib.sitemaps",
]

INSTALLED_APPS = [*DJANGO_APPS, *LOCAL_APPS, *THIRD_PARTY_APPS]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "crypto_spotlight.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "crypto_spotlight.context_processors.website_name",
                "crypto_spotlight.context_processors.website_domain",
                "crypto_spotlight.context_processors.model_name",
                "crypto_spotlight.context_processors.website_twitter",
                "crypto_spotlight.context_processors.website_linkedin",
            ],
        },
    },
]

WSGI_APPLICATION = "crypto_spotlight.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
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
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "crypto_spotlight", "static"),
]

# Media files (Uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Text Generation Service
MODEL_NAME = os.getenv("MODEL_NAME")
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")

# Contexts
WEBSITE_NAME = os.getenv("WEBSITE_NAME")
WEBSITE_DOMAIN = os.getenv("WEBSITE_DOMAIN")
WEBSITE_TWITTER = os.getenv("WEBSITE_TWITTER")
WEBSITE_LINKEDIN = os.getenv("WEBSITE_LINKEDIN")

# Sitemap
SITEMAP_LIMIT = int(os.getenv("SITEMAP_LIMIT", 50))

# RSS
RSS_FEED_LIMIT = int(os.getenv("RSS_FEED_LIMIT", 50))

# Posts
MAX_POSTS_PER_CATEGORY_LIMIT = int(os.getenv("MAX_POSTS_PER_CATEGORY_LIMIT", 16))
MAX_ITEM_SIDEBAR_WIDGET_LIMIT = int(os.getenv("MAX_ITEM_SIDEBAR_WIDGET_LIMIT", 5))
POSTS_PER_PAGE_LIMIT = int(os.getenv("POSTS_PER_PAGE_LIMIT", 16))

# Donate wallet address
DONATE_BITCOIN_ADDRESS = os.getenv("DONATE_BITCOIN_ADDRESS")
DONATE_ETHEREUM_ADDRESS = os.getenv("DONATE_ETHEREUM_ADDRESS")
