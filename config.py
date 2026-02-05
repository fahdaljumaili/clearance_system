# config.py

import os
import json

# مسار مجلد المشروع الحالي (حيث يوجد هذا الملف)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# مسار ملف مفاتيح VAPID داخل مجلد instance
VAPID_KEYS_PATH = os.path.join(BASE_DIR, 'instance', 'vapid_keys.json')

# تحميل المفاتيح من الملف
with open(VAPID_KEYS_PATH, 'r', encoding='utf-8') as f:
    vapid_keys = json.load(f)

# تعريف المتغيرات لاستخدامها في التطبيق
VAPID_PUBLIC_KEY = vapid_keys.get('publicKey')
VAPID_PRIVATE_KEY = vapid_keys.get('privateKey')
VAPID_EMAIL = "example@example.com"  # غيّره إلى بريدك الحقيقي

# إعدادات البريد الإلكتروني (Flask-Mail)
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'example@example.com'
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'example'
