from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.session.execute(text("UPDATE user SET role='section_head' WHERE role='department_officer'"))
    db.session.commit()
    print("Migration successful. All 'department_officer' roles updated to 'section_head'.")
