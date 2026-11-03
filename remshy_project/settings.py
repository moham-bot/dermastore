import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-remshy-medical-store-secret-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',') if h.strip()]
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.inlines',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'remshy_project.urls'

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
                'store.context_processors.cart_context',
                'store.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'remshy_project.wsgi.application'

# Database — SQLite locally, PostgreSQL via DATABASE_URL env var
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    import urllib.parse as urlparse
    url = urlparse.urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port or 5432,
            'OPTIONS': {'sslmode': 'require'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'aeildie1')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '477871866486762')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET,
}

if CLOUDINARY_API_SECRET:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Business settings
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '967778550938')

# Unfold Admin configuration
UNFOLD = {
    "SITE_TITLE": "متجر ريمشي الطبي",
    "SITE_HEADER": "لوحة تحكم ريمشي",
    "SITE_URL": "/",
    "SITE_SYMBOL": "medication",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "STYLES": [
        lambda request: "/static/css/admin_theme.css",
    ],
    "COLORS": {
        "font": {
            "subtle-light": "102 115 109",
            "subtle-dark": "156 163 175",
            "default-light": "38 51 47",
            "default-dark": "243 244 246",
            "important-light": "38 51 47",
            "important-dark": "243 244 246",
        },
        "primary": {
            "50": "240 245 243",
            "100": "220 231 226",
            "200": "194 214 206",
            "300": "160 188 178",
            "400": "128 162 150",
            "500": "111 143 130",
            "600": "85 119 108",
            "700": "63 94 85",
            "800": "53 92 82",
            "900": "38 51 47",
            "950": "20 30 27",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "المتجر",
                "separator": True,
                "items": [
                    {
                        "title": "المنتجات",
                        "icon": "medication",
                        "link": "/admin/store/product/",
                    },
                    {
                        "title": "الباقات الجاهزة",
                        "icon": "inventory_2",
                        "link": "/admin/store/routinebundle/",
                    },
                    {
                        "title": "الطلبات",
                        "icon": "shopping_cart",
                        "link": "/admin/store/order/",
                    },
                ],
            },
            {
                "title": "قاعدة البيانات العلمية",
                "separator": True,
                "items": [
                    {
                        "title": "أنواع البشرة",
                        "icon": "face",
                        "link": "/admin/store/skintype/",
                    },
                    {
                        "title": "مشاكل البشرة",
                        "icon": "healing",
                        "link": "/admin/store/skinconcern/",
                    },
                    {
                        "title": "المواد الفعالة",
                        "icon": "science",
                        "link": "/admin/store/activeingredient/",
                    },
                ],
            },
            {
                "title": "الإدارة",
                "separator": True,
                "items": [
                    {
                        "title": "المستخدمون",
                        "icon": "person",
                        "link": "/admin/auth/user/",
                    },
                ],
            },
        ],
    },
}
