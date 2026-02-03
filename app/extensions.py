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
    'مجانية التعليم', 'معاون العميد للشؤون العلمية', 'القسم العلمي',
    'الأقسام الداخلية', 'الهويات', 'الوحدة الرياضية',
    'المكتبة المركزية', 'مكتبة الكلية', 'الحسابات', 'التسجيل'
]
