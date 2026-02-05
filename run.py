from app import create_app
from app.extensions import db
from app.models import User


# إنشاء كائن التطبيق باستخدام دالة المصنع
app = create_app()

# التأكد من وجود سياق التطبيق للتعامل مع قاعدة البيانات
with app.app_context():
    # إنشاء الجداول في قاعدة البيانات إن لم تكن موجودة مسبقاً
    db.create_all()

    # التحقق من وجود مستخدم مدير، وإنشاؤه تلقائياً إذا لم يكن موجوداً
    if not User.query.filter_by(role='system_admin').first():
        print("Creating default admin user...")
        admin = User(
            username='admin',
            email='admin@example.com',
            role='system_admin',
            full_name='System Administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: admin / admin123")



if __name__ == '__main__':
    # تشغيل التطبيق في وضع التصحيح (Debug Mode)
    app.run(debug=True)
