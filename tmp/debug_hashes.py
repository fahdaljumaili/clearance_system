import sqlite3
import os
import sys

# إضافة مسار المشروع للاستيراد
sys.path.append(os.getcwd())

from app import create_app
from app.models import User
from app.extensions import db

def check_diff():
    app = create_app()
    with app.app_context():
        # 1. جلب الهاش من SQLite
        conn_sq = sqlite3.connect('instance/database.db')
        cur_sq = conn_sq.cursor()
        cur_sq.execute('SELECT password_hash FROM user WHERE university_id="123456789"')
        row_sq = cur_sq.fetchone()
        hash_sq = row_sq[0] if row_sq else "NOT FOUND"
        
        # 2. جلب الهاش من MySQL
        u_my = User.query.filter_by(university_id='123456789').first()
        hash_my = u_my.password_hash if u_my else "NOT FOUND"
        
        print(f"SQLite Hash Length: {len(hash_sq)}")
        print(f"MySQL Hash Length : {len(hash_my)}")
        print(f"Hashes Identical? : {hash_sq == hash_my}")
        
        if u_my:
            print(f"Check Password '123456789' in MySQL Context: {u_my.check_password('123456789')}")
        
        # تجربة فحص الهاش الأصلي يدوياً باستخدام Werkzeug
        from werkzeug.security import check_password_hash
        print(f"Manual check of SQLite hash: {check_password_hash(hash_sq, '123456789')}")
        print(f"Manual check of MySQL hash : {check_password_hash(hash_my, '123456789')}")

if __name__ == '__main__':
    check_diff()
