from app import create_app
from app.extensions import db
from app.models import User


# إنشاء كائن التطبيق باستخدام دالة المصنع
app = create_app()

# التأكد من وجود سياق التطبيق للتعامل مع قاعدة البيانات
with app.app_context():
    # إنشاء الجداول في قاعدة البيانات إن لم تكن موجودة مسبقاً
    db.create_all()

    # إضافة عمود temp_password إذا لم يكن موجوداً (ترقية قاعدة البيانات)
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('user')]
    if 'temp_password' not in columns:
        db.session.execute(text('ALTER TABLE user ADD COLUMN temp_password VARCHAR(50)'))
        db.session.commit()
        print("Added temp_password column to user table.")

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
