from app import create_app
from app.extensions import db

# إنشاء كائن التطبيق باستخدام دالة المصنع
app = create_app()

# التأكد من وجود سياق التطبيق للتعامل مع قاعدة البيانات
with app.app_context():
    # إنشاء الجداول في قاعدة البيانات إن لم تكن موجودة مسبقاً
    db.create_all()


if __name__ == '__main__':
    # تشغيل التطبيق في وضع التصحيح (Debug Mode)
    app.run(debug=True)
