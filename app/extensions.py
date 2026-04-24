"""
app/extensions.py
الغاية من الملف:
تعريف الإضافات والمكتبات المستخدمة في المشروع (مثل قاعدة البيانات، والبريد) بشكل مستقل.
الهدف من هذا الملف هو منع حدوث مشكلة "الاستدعاء الدائري" (Circular Imports) بين الملفات الأخرى.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

# تهيئة كائن قاعدة البيانات (SQLAlchemy)
db = SQLAlchemy()

# تهيئة مدير تسجيل الدخول (LoginManager) لإدارة جلسات المستخدمين
login_manager = LoginManager()

# تهيئة حماية CSRF لمنع هجمات تزوير الطلبات عبر المواقع
csrf = CSRFProtect()

# تهيئة نظام البريد الإلكتروني (Flask-Mail)
mail = Mail()

# قائمة بالأقسام المتاحة في النظام لاستخدامها في القوائم المنسدلة والتحقق
DEPARTMENTS = [
    'مجانية التعليم', 'معاون العميد للشؤون العلمية', 'الشعبة العلمية',
    'الأقسام الداخلية', 'الهويات', 'الوحدة الرياضية',
    'المكتبة المركزية', 'مكتبة الكلية', 'الحسابات', 'التسجيل'
]
