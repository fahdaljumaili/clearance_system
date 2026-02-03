import os
from flask import Flask
from .routes import main_routes
from .extensions import db, login_manager, csrf, mail
from .models import User
from datetime import datetime, timedelta

# مرشح (Filter) لتنسيق الوقت في Jinja2
def format_local_time(utc_dt):
    """ يحول الوقت من UTC إلى التوقيت المحلي (GMT+3)."""
    if not utc_dt:
        return ""
    # إضافة 3 ساعات للتوقيت المحلي
    local_dt = utc_dt + timedelta(hours=3)
    return local_dt.strftime('%Y-%m-%d %H:%M')

# دالة مصنع التطبيق (Application Factory)
def create_app():
    # تحديد مسار المجلد الجذري للمشروع
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # تهيئة تطبيق Flask مع تحديد مجلد الملفات الثابتة (static)
    app = Flask(
        __name__,
        static_folder=os.path.join(root, 'static'),
        static_url_path=''
    )
    
    # تحميل الإعدادات من ملف التكوين
    app.config.from_object('config')
    # تعيين المفتاح السري (يجب تغييره في بيئة الإنتاج)
    app.config['SECRET_KEY'] = '4a8a6021f1e313a3f4e1f7d2f9d7c8c8b6a3e1d1f2a3a1b5'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/database.db'
    
    # تهيئة الإضافات (Extensions) مع التطبيق
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)  # تفعيل حماية CSRF
    mail.init_app(app)
    
    # تعيين عرض تسجيل الدخول لإعادة التوجيه عند الحاجة
    login_manager.login_view = 'main.login'
    
    # دالة تحميل المستخدم لجلسة تسجيل الدخول
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # تسجيل المخطط الرئيسي للمسارات
    app.register_blueprint(main_routes)
    
    # إضافة مرشحات مخصصة لـ Jinja2
    app.jinja_env.filters['local_time'] = format_local_time
    
    # إضافة متغيرات سياق عامة لجميع القوالب
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
        
    return app