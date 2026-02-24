from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from datetime import datetime


# نموذج المستخدم (User Model)
# يمثل جدول المستخدمين في قاعدة البيانات ويحتوي على بيانات الطلاب والموظفين والمدراء
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.String(20), unique=True, nullable=True)  # الرقم الجامعي (خاص بالطلاب)
    username = db.Column(db.String(50), unique=True, nullable=True)       # اسم المستخدم (للموظفين والمدراء)
    email = db.Column(db.String(120), unique=True, nullable=True)         # البريد الإلكتروني
    password_hash = db.Column(db.String(128), nullable=False)             # كلمة المرور المشفرة
    role = db.Column(db.String(20), nullable=False)  # دور المستخدم: 'student', 'system_admin', 'department_officer'
    full_name = db.Column(db.String(100), nullable=True) # الاسم الكامل (للعرض فقط)
    department = db.Column(db.String(100), nullable=True) # القسم (للموظفين والطلاب)
    stage = db.Column(db.String(50), nullable=True)       # المرحلة الدراسية (للطلاب)
    study_type = db.Column(db.String(50), nullable=True)  # نوع الدراسة: صباحي/مسائي (للطلاب)
    temp_password = db.Column(db.String(50), nullable=True) # كلمة المرور المؤقتة (تظهر للمدير فقط)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # تاريخ إنشاء الحساب

    # خاصية لعرض الاسم المناسب حسب دور المستخدم
    @property
    def display_name(self):
        # إذا كان طالبًا يتم عرض الرقم الجامعي، وإلا يتم عرض اسم المستخدم
        return self.university_id if self.role == 'student' else self.username

    # دالة لتعيين كلمة المرور (تقوم بإنشاء تجزئة التشفير)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # دالة للتحقق من كلمة المرور عند تسجيل الدخول
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # دالة لإنشاء رمز إعادة تعيين كلمة المرور (صالح لمدة معينة)
    def get_reset_token(self, expires_sec=1800):
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    # دالة ثابتة للتحقق من رمز إعادة تعيين كلمة المرور وإرجاع المستخدم
    @staticmethod
    def verify_reset_token(token):
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            # محاولة فك تشفير الرمز والحصول على معرف المستخدم
            user_id = s.loads(token, salt='password-reset-salt', max_age=1800)['user_id']
        except:
            return None
        return User.query.get(user_id)


# نموذج حالة براءة الذمة (ClearanceStatus Model)
# يخزن حالة براءة الذمة للطالب في كل قسم
class ClearanceStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # معرف الطالب
    department = db.Column(db.String(100), nullable=False)  # اسم القسم المعني بالموافقة
    status = db.Column(db.String(20), default='pending')  # الحالة: pending (قيد الانتظار), approved (موافق عليه), rejected (مرفوض)
    comment = db.Column(db.Text, nullable=True) # ملاحظات مسؤول القسم
    updated_at = db.Column(db.DateTime, default=datetime.utcnow) # تاريخ آخر تحديث

    # علاقة مع نموذج المستخدم (الطالب)
    student = db.relationship('User', backref='clearance_statuses')


# نموذج الإشعارات (Notification Model)
# يخزن الإشعارات الموجهة للمستخدمين
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # معرف المستخدم المستلم للإشعار
    message = db.Column(db.String(255), nullable=False) # نص الإشعار
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # وقت الإشعار
    is_read = db.Column(db.Boolean, default=False) # هل تمت قراءة الإشعار أم لا

    # علاقة مع نموذج المستخدم
    user = db.relationship('User', backref='notifications')


# نموذج اشتراكات الإشعارات الفورية (PushSubscription Model)
# يخزن بيانات الاشتراك لخدمة Web Push Notifications
class PushSubscription(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # معرف المستخدم
    endpoint  = db.Column(db.Text,    nullable=False) # نقطة النهاية لإرسال الإشعار
    p256dh    = db.Column(db.Text,    nullable=False) # مفتاح التشفير العام
    auth      = db.Column(db.Text,    nullable=False) # مفتاح المصادقة
    created_at= db.Column(db.DateTime, default=datetime.utcnow) # تاريخ الاشتراك

    # علاقة مع نموذج المستخدم
    user      = db.relationship('User', backref='push_subscriptions')
