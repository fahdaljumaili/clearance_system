import sqlite3
import pymysql
from app import create_app
from app.extensions import db
from app.models import User, ClearanceStatus, Notification, PushSubscription
from sqlalchemy import text

def migrate():
    print("Starting migration from SQLite to MySQL...")
    app = create_app()
    with app.app_context():
        # 1. إنشاء الجداول في MySQL
        db.create_all()
        print("MySQL tables created/verified.")
        
        # 2. الاتصال بـ SQLite
        sqlite_path = 'instance/database.db'
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # 3. نقل البيانات لجدول المستخدمين (User)
        sqlite_cursor.execute("SELECT * FROM user")
        users = sqlite_cursor.fetchall()
        for u in users:
            u_data = dict(u)
            existing = User.query.get(u_data['id'])
            if existing:
                existing.password_hash = u_data['password_hash']
            else:
                new_user = User(**u_data)
                db.session.add(new_user)
        db.session.commit()
        print(f"Migrated {len(users)} users.")

        # 4. نقل البيانات لجدول ClearanceStatus
        sqlite_cursor.execute("SELECT * FROM clearance_status")
        records = sqlite_cursor.fetchall()
        for r in records:
            r_data = dict(r)
            if not ClearanceStatus.query.get(r_data['id']):
                db.session.add(ClearanceStatus(**r_data))
        db.session.commit()
        print(f"Migrated {len(records)} clearance records.")

        # 5. نقل البيانات لجدول Notification
        sqlite_cursor.execute("SELECT * FROM notification")
        notifs = sqlite_cursor.fetchall()
        for n in notifs:
            n_data = dict(n)
            # التعامل مع الحقل المنطقي (sqlite يخزنه 0/1)
            n_data['is_read'] = bool(n_data['is_read'])
            if not Notification.query.get(n_data['id']):
                db.session.add(Notification(**n_data))
        db.session.commit()
        print(f"Migrated {len(notifs)} notifications.")

        # 6. نقل البيانات لجدول PushSubscription
        sqlite_cursor.execute("SELECT * FROM push_subscription")
        subs = sqlite_cursor.fetchall()
        for s in subs:
            s_data = dict(s)
            if not PushSubscription.query.get(s_data['id']):
                db.session.add(PushSubscription(**s_data))
        db.session.commit()
        print(f"Migrated {len(subs)} push subscriptions.")

        print("Migration completed successfully! 🚀")

if __name__ == '__main__':
    migrate()
