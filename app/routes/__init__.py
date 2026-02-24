import os
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app

from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# تجميع كل الاستيرادات من داخل التطبيق هنا
from app.extensions import db, DEPARTMENTS, csrf, mail
from app.models import User, ClearanceStatus, Notification, PushSubscription
from app.forms import LoginForm, UpdateStatusForm, ClearanceRequestForm, RequestResetForm, ResetPasswordForm, AddUserForm, EditUserForm
from app.utils.push_notifications import send_push_to_subscription
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

# تعريف المخطط (Blueprint) للمسارات الرئيسية
main_routes = Blueprint('main', __name__)


# الصفحة الرئيسية / نقطة الدخول
@main_routes.route('/')
def home():
    """يعرض صفحة تسجيل الدخول أو يوجه المستخدم للوحة التحكم المناسبة إذا كان مسجلاً للدخول بالفعل."""
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('main.student'))
        elif current_user.role == 'department_officer':
            return redirect(url_for('main.department_officer'))
        elif current_user.role == 'system_admin':
            return redirect(url_for('main.system_administrator'))
            
    # إذا لم يكن مسجلاً، عرض نموذج تسجيل الدخول
    form = LoginForm()
    return render_template('login.html', form=form)


# مسار تسجيل الدخول
@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    """يتعامل مع عملية تسجيل الدخول والتحقق من البيانات."""
    # إذا كان المستخدم مسجل الدخول، قم بتسجيل خروجه فوراً لضمان أمان الجلسة
    if current_user.is_authenticated:
        logout_user()
        
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data
        
        # البحث عن المستخدم بالرقم الجامعي أو اسم المستخدم
        user = User.query.filter_by(university_id=identifier).first() or User.query.filter_by(username=identifier).first()
        
        if user and user.check_password(password):
            login_user(user)
            # التوجيه حسب الدور الجديد
            if user.role == 'student':
                return redirect(url_for('main.student'))
            elif user.role == 'department_officer':
                return redirect(url_for('main.department_officer'))
            elif user.role == 'system_admin':
                return redirect(url_for('main.system_administrator'))
        
        flash('البيانات المدخلة غير صحيحة', 'danger')
    
    return render_template('login.html', form=form)


# مسار تسجيل الخروج
@main_routes.route('/logout')
@login_required
def logout():
    """يتعامل مع عملية تسجيل الخروج."""
    logout_user()
    return redirect(url_for('main.login'))


# لوحة تحكم الطالب
@main_routes.route('/student')
@login_required
def student():
    """يعرض لوحة تحكم الطالب وحالة طلبات براءة الذمة."""
    if current_user.role != 'student':
        return redirect(url_for('main.login'))
        
    # جلب سجلات براءة الذمة الخاصة بالطالب
    records = ClearanceStatus.query.filter_by(student_id=current_user.id).all()
    # التحقق مما إذا كانت جميع الموافقات مقبولة
    all_app = all(r.status == 'approved' for r in records)
    form = ClearanceRequestForm() 
    
    return render_template(
        'student.html',
        student=current_user,
        clearance_records=records,
        all_approved=all_app,
        vapid_public_key=current_app.config.get('VAPID_PUBLIC_KEY'),
        DEPARTMENTS=DEPARTMENTS,
        form=form 
    )


# لوحة تحكم مدير النظام
@main_routes.route('/system_administrator', methods=['GET', 'POST'])
@login_required
def system_administrator():
    """يعرض لوحة تحكم مدير النظام، إدارة الطلاب والمستخدمين."""
    if current_user.role != 'system_admin':
        return redirect(url_for('main.login'))

    # جلب قائمة الطلاب
    students = User.query.filter_by(role='student').all()
    
    # حساب الإحصائيات
    total_students = len(students)
    completed_count = 0
    pending_count = 0
    
    # تهيئة عداد الأقسام للمعلقات
    pending_by_dept = {dept: 0 for dept in DEPARTMENTS}

    for student in students:
        student.records = ClearanceStatus.query.filter_by(student_id=student.id).order_by(ClearanceStatus.department).all()
        
        # التحقق من اكتمال براءة الذمة للطالب
        is_completed = (
            student.records 
            and len(student.records) == len(DEPARTMENTS) 
            and all(r.status == 'approved' for r in student.records)
        )
        
        if is_completed:
            completed_count += 1
            student.final_status = 'مكتمل'
        else:
            pending_count += 1
            student.final_status = 'غير مكتمل'
            
            # حساب الأقسام التي لم توافق بعد
            for r in student.records:
                if r.status == 'pending':
                    if r.department in pending_by_dept:
                        pending_by_dept[r.department] += 1

    # --- منطق إدارة المستخدمين ---
    user_form = AddUserForm()
    active_tab = 'analytics'

    # معالجة نموذج إضافة مستخدم جديد
    if 'submit' in request.form:
        if user_form.validate_on_submit():
            hashed_pw = generate_password_hash(user_form.password.data)
            new_user = User(
                username=user_form.username.data if user_form.role.data != 'student' else None,
                full_name=user_form.full_name.data,
                email=user_form.email.data,
                password_hash=hashed_pw,
                role=user_form.role.data,
                university_id=user_form.university_id.data if user_form.role.data == 'student' else None,
                department=user_form.department.data if (user_form.role.data == 'department_officer' or user_form.role.data == 'student') else None,
                stage=user_form.stage.data if user_form.role.data == 'student' else None,
                study_type=user_form.study_type.data if user_form.role.data == 'student' else None
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                flash(f'تم إضافة المستخدم {new_user.full_name or new_user.username} بنجاح', 'success')
                return redirect(url_for('main.system_administrator')) # نمط Post-Redirect-Get
            except Exception as e:
                db.session.rollback()
                flash(f'خطأ أثناء الإضافة: {str(e)}', 'danger')
        else:
            active_tab = 'users'

    all_users = User.query.order_by(User.id.asc()).all()
    edit_user_form = EditUserForm() # تهيئة نموذج التعديل لاستخدامه في النافذة المنبثقة

    return render_template(
        'system_administrator.html',
        students=students,
        vapid_public_key=current_app.config.get('VAPID_PUBLIC_KEY'),
        total_students=total_students,
        completed_count=completed_count,
        pending_count=pending_count,
        pending_by_dept=pending_by_dept,
        DEPARTMENTS=DEPARTMENTS, 
        user_form=user_form,
        edit_user_form=edit_user_form,
        all_users=all_users,
        active_tab=active_tab
    )

# لوحة تحكم مسؤول القسم
@main_routes.route('/department_officer')
@login_required
def department_officer():
    """يعرض لوحة تحكم مسؤول القسم لمراجعة طلبات الطلاب."""
    if current_user.role != 'department_officer':
        return redirect(url_for('main.login'))
    
    # جلب الطلبات الخاصة بقسم المسؤول الحالي فقط
    records = ClearanceStatus.query.filter_by(department=current_user.department).all()
    form = UpdateStatusForm()
    return render_template(
        'department_officer.html', 
        records=records, 
        form=form, 
        vapid_public_key=current_app.config.get('VAPID_PUBLIC_KEY')
    )


# مسار تعديل بيانات المستخدم
@main_routes.route('/user/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    """يسمح للمدير بتعديل بيانات المستخدم."""
    if current_user.role != 'system_admin': # فقط مدير النظام يمكنه التعديل
        flash('غير مصرح لك بالقيام بهذا الإجراء.', 'danger')
        return redirect(url_for('main.home'))

    user = User.query.get_or_404(user_id)
    form = EditUserForm()

    if form.validate_on_submit():
        user.username = form.username.data if form.role.data != 'student' else None
        user.full_name = form.full_name.data
        user.email = form.email.data
        user.role = form.role.data
        user.university_id = form.university_id.data or None
        user.department = form.department.data or None
        if form.role.data == 'student':
            user.stage = form.stage.data
            user.study_type = form.study_type.data
        else:
            user.stage = None
            user.study_type = None
        
        # تحديث كلمة المرور فقط إذا تم إدخال قيمة جديدة
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
            
        try:
            db.session.commit()
            flash('تم تحديث بيانات المستخدم بنجاح.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء التحديث: {e}', 'danger')
            
    return redirect(url_for('main.system_administrator'))


# تحديث حالة الطالب من قبل مسؤول القسم
@main_routes.route('/update_status', methods=['POST'])
@login_required
def update_status():
    """يتعامل مع تحديث مسؤول القسم لحالة الطالب."""
    form = UpdateStatusForm()
    student_id = request.form.get('student_id')
    department = request.form.get('department')
    rec = ClearanceStatus.query.filter_by(student_id=student_id, department=department).first()

    if not rec:
        flash('السجل غير موجود', 'danger')
        # توجيه ذكي حسب الدور
        if current_user.role == 'system_admin':
            return redirect(url_for('main.system_administrator'))
        return redirect(url_for('main.department_officer'))

    if form.validate_on_submit():
        rec.status = form.status.data
        rec.comment = form.comment.data
        rec.updated_at = datetime.utcnow()
        
        # --- التنبيه الداخلي (Notification) ---
        student_notification = Notification(
            user_id=student_id,
            message=f"قسم {rec.department} غيّر حالتك إلى {rec.status}"
        )
        db.session.add(student_notification)

        # --- التنبيه الفوري (Push Notification) للويب ---
        student_subs = PushSubscription.query.filter_by(user_id=student_id).all()
        for s in student_subs:
            send_push_to_subscription(
                sub_info={ "endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth} },
                payload={ "title": "تحديث الحالة", "body": f"قسم {rec.department} غيّر حالتك إلى {rec.status}" }
            )
        
        # --- البريد الإلكتروني ---
        student_user = User.query.get(student_id)
        if student_user and student_user.email:
            try:
                send_status_email(student_user, rec.department, rec.status, rec.comment)
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        # تنظيف الإشعارات القديمة عند المسؤول
        if student_user:
            message_content = f"طلب براءة ذمة جديد من الطالب {student_user.university_id}."
            notifications_to_read = Notification.query.filter_by(
                user_id=current_user.id,
                message=message_content,
                is_read=False
            ).all()
            
            for notif in notifications_to_read:
                notif.is_read = True
        
        db.session.commit()
        flash('تم تحديث الحالة بنجاح', 'success')
    else:
        flash('حدث خطأ أثناء تحديث الحالة. يرجى المحاولة مرة أخرى.', 'danger')

    if current_user.role == 'system_admin':
        return redirect(url_for('main.system_administrator'))
    return redirect(url_for('main.department_officer'))


# حذف مستخدم
@main_routes.route('/system_admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """يحذف مستخدم من النظام مع تنظيف البيانات المرتبطة به."""
    if current_user.role != 'system_admin':
        flash('غير مصرح لك بهذا الإجراء', 'danger')
        return redirect(url_for('main.home'))
        
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الحالي', 'warning')
    else:
        try:
            # تنظيف البيانات المرتبطة
            if user.role == 'student':
                ClearanceStatus.query.filter_by(student_id=user.id).delete()
            
            # حذف الإشعارات والاشتراكات المرتبطة لتجنب خطأ التكامل المرجعي
            Notification.query.filter_by(user_id=user.id).delete()
            PushSubscription.query.filter_by(user_id=user.id).delete()
                
            db.session.delete(user)
            db.session.commit()
            flash('تم حذف المستخدم بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'فشل الحذف. قد تكون هناك بيانات مرتبطة: {str(e)}', 'danger')
            
    return redirect(url_for('main.system_administrator'))


# تقديم طلب براءة ذمة
@main_routes.route('/request_clearance', methods=['POST'])
@login_required
def request_clearance():
    """يتعامل مع طلب الطالب لبدء إجراءات براءة الذمة."""
    form = ClearanceRequestForm()
    if current_user.role != 'student':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('main.login'))

    if form.validate_on_submit():
        existing = ClearanceStatus.query.filter_by(student_id=current_user.id).first()
        if existing:
            flash('لقد أرسلت طلبًا سابقًا.', 'warning')
            return redirect(url_for('main.student'))

        # إنشاء سجل لكل قسم
        for dept_name in DEPARTMENTS:
            db.session.add(ClearanceStatus(
                student_id=current_user.id,
                department=dept_name,
                status='pending'
            ))

            # البحث عن مسؤول القسم وتنبيهه
            officer_user = User.query.filter_by(role='department_officer', department=dept_name).first()
            if officer_user:
                
                message_content = f"طلب براءة ذمة جديد من الطالب {current_user.university_id}."
                
                admin_notification = Notification(
                    user_id=officer_user.id,
                    message=message_content
                )
                db.session.add(admin_notification)
                
                admin_subs = PushSubscription.query.filter_by(user_id=officer_user.id).all()
                for sub in admin_subs:
                    send_push_to_subscription(
                        sub_info={ "endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth} },
                        payload={ "title": "طلب براءة ذمة جديد", "body": message_content }
                    )

        db.session.commit() 
        flash('📨 تم تقديم طلب براءة الذمة بنجاح.', 'success')
    else:
        flash('حدث خطأ غير متوقع، يرجى المحاولة مرة أخرى.', 'danger')

    return redirect(url_for('main.student'))


# حفظ اشتراك الإشعارات
@main_routes.route('/save-subscription', methods=['POST'])
@csrf.exempt 
@login_required
def save_subscription():
    """يحفظ اشتراك الإشعار الفوري للمستخدم لتمكينه من استلام التنبيهات لاحقاً."""
    data = request.get_json()
    if not data or 'endpoint' not in data:
        return jsonify({'status':'bad request'}), 400
        
    existing = PushSubscription.query.filter_by(user_id=current_user.id, endpoint=data['endpoint']).first()
    if existing:
        return jsonify({'status':'exists'})
    sub = PushSubscription(
        user_id=current_user.id,
        endpoint=data['endpoint'],
        p256dh=data['keys']['p256dh'],
        auth=data['keys']['auth']
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({'status':'saved'})


# حذف اشتراك الإشعارات
@main_routes.route('/delete-subscription', methods=['POST'])
@csrf.exempt 
@login_required
def delete_subscription():
    """يحذف اشتراك الإشعار الفوري للمستخدم."""
    endpoint = request.get_json().get('endpoint')
    if not endpoint:
        return jsonify({'status':'bad request'}), 400
        
    PushSubscription.query.filter_by(user_id=current_user.id, endpoint=endpoint).delete()
    
    db.session.commit()
    return jsonify({'status': 'subscription deleted'})


# تعليم الإشعارات كمقروءة
@main_routes.route('/notifications/mark_read')
@login_required
def mark_notifications_read():
    """يجعل كل الإشعارات الداخلية للمستخدم مقروءة."""
    for n in current_user.notifications:
        n.is_read = True
    db.session.commit()
    
    if current_user.role == 'student':
        return redirect(url_for('main.student'))
    elif current_user.role == 'department_officer':
        return redirect(url_for('main.department_officer'))
    else:
        return redirect(url_for('main.system_administrator'))


# تنزيل نموذج براءة الذمة
@main_routes.route('/download_clearance_form')
@login_required
def download_clearance_form():
    """يعرض صفحة طباعة براءة الذمة للطالب (فقط عند اكتمال الموافقات)."""
    if current_user.role != 'student':
        flash('غير مصرح لك بتنزيل النموذج', 'danger')
        return redirect(url_for('main.login'))
        
    records = ClearanceStatus.query.filter_by(student_id=current_user.id).all()
    all_approved = all(r.status == 'approved' for r in records)
    
    if not all_approved:
        flash('لا يمكنك تنزيل النموذج قبل اكتمال جميع الموافقات', 'warning')
        return redirect(url_for('main.student'))
        
    return render_template('clearance_form.html', student=current_user, records=records)

# --- دوال المساعدة للبريد الإلكتروني ---

def send_status_email(user, department, status, comment=None):
    """إرسال بريد إلكتروني للطالب عند تحديث حالته."""
    status_ar = "مقبول" if status == "approved" else "مرفوض" if status == "rejected" else "قيد المعالجة"
    msg = Message(f'تحديث حالة براءة الذمة - {department}',
                  sender=current_app.config.get('MAIL_USERNAME'),
                  recipients=[user.email])
    
    msg.body = f'''مرحباً {user.full_name or user.username}،

لقد قام قسم {department} بتحديث حالة طلبك إلى: {status_ar}

{f"ملاحظات: {comment}" if comment else ""}

يرجى مراجعة حسابك للمزيد من التفاصيل.
'''
    mail.send(msg)

def send_reset_email(user):
    """إرسال بريد استعادة كلمة المرور."""
    token = user.get_reset_token()
    msg = Message('طلب استعادة كلمة المرور',
                  sender=current_app.config.get('MAIL_USERNAME'),
                  recipients=[user.email])
    msg.body = f'''لإعادة تعيين كلمة المرور، يرجى زيارة الرابط التالي:
{url_for('main.reset_token', token=token, _external=True)}

إذا لم تطلب هذا التغيير، فتجاهل هذه الرسالة ولن يحدث أي تغيير.
'''
    mail.send(msg)

# طلب إعادة تعيين كلمة المرور
@main_routes.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        logout_user()
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('تم إرسال بريد إلكتروني بتعليمات إعادة تعيين كلمة المرور.', 'info')
        return redirect(url_for('main.login'))
    return render_template('reset_request.html', title='استعادة كلمة المرور', form=form)

# تعيين كلمة مرور جديدة عبر التوكن
@main_routes.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        logout_user()
    user = User.verify_reset_token(token)
    if user is None:
        flash('الرابط غير صالح أو انتهت صلاحيته', 'warning')
        return redirect(url_for('main.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('تم تحديث كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_token.html', title='تعيين كلمة المرور', form=form)


# زر خاص لمدير النظام لتصفير البيانات (لبدء دورة جديدة)
@main_routes.route('/system_admin/reset_all_clearances', methods=['POST'])
@login_required
def reset_all_clearances():
    """يحذف جميع سجلات براءة الذمة لبدء دورة جديدة."""
    if current_user.role != 'system_admin':
        flash('غير مصرح لك بهذا الإجراء', 'danger')
        return redirect(url_for('main.home'))

    try:
        # حذف جميع السجلات من جدول ClearanceStatus
        num_deleted_clearances = db.session.query(ClearanceStatus).delete()
        
        # حذف جميع الإشعارات (اختياري حسب الطلب)
        num_deleted_notifications = db.session.query(Notification).delete()
        
        db.session.commit()
        flash(f'تم بدء دورة جديدة. تم حذف {num_deleted_clearances} سجل براءة ذمة و {num_deleted_notifications} إشعار.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إعادة التعيين: {str(e)}', 'danger')

    return redirect(url_for('main.system_administrator'))

@main_routes.route('/system_admin/import_students', methods=['POST'])
@login_required
def import_students():
    if current_user.role != 'system_admin':
        abort(403)

    if 'file' not in request.files:
        flash('لم يتم اختيار ملف', 'danger')
        return redirect(url_for('main.system_administrator', active_tab='users'))

    file = request.files['file']
    if file.filename == '':
        flash('لم يتم اختيار ملف', 'danger')
        return redirect(url_for('main.system_administrator', active_tab='users'))

    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        try:
            # قراءة ملف الإكسل باستخدام pandas
            df = pd.read_excel(file)
            
            # تنظيف أسماء الأعمدة (إزالة المسافات الزائدة)
            df.columns = df.columns.str.strip()

            # التحقق من الأعمدة المطلوبة
            required_columns = ['الرقم الجامعي', 'الاسم الكامل']
            if not all(col in df.columns for col in required_columns):
                flash(f'الملف يجب أن يحتوي على الأعمدة التالية: {", ".join(required_columns)}', 'danger')
                return redirect(url_for('main.system_administrator', active_tab='users'))

            success_count = 0
            errors = []
            imported_passwords = []

            for index, row in df.iterrows():
                try:
                    uni_id = str(row['الرقم الجامعي']).strip()
                    full_name = str(row['الاسم الكامل']).strip()
                    
                    # دالة مساعدة لجلب القيمة من عدة احتمالات لاسم العمود
                    def get_val(possible_cols):
                        for col in possible_cols:
                            if col in df.columns and pd.notna(row[col]):
                                return str(row[col]).strip()
                        return None

                    email = get_val(['البريد الإلكتروني', 'البريد الالكتروني', 'email', 'Email'])
                    department = get_val(['القسم', 'department', 'Department'])
                    stage = get_val(['المرحلة', 'stage', 'Stage'])
                    study_type = get_val(['نوع الدراسة', 'نوع الدراسة', 'Study Type'])

                    # التحقق مما إذا كان الطالب موجوداً مسبقاً
                    existing_user = User.query.filter_by(university_id=uni_id).first()
                    if existing_user:
                        errors.append(f"الطالب {uni_id} موجود مسبقاً.")
                        continue

                    # توليد كلمة مرور قوية عشوائية (12 حرف)
                    import string, random
                    chars = string.ascii_letters + string.digits + '!@#$%&*'
                    generated_password = ''.join(random.choice(chars) for _ in range(12))

                    # إنشاء حساب جديد
                    new_student = User(
                        university_id=uni_id,
                        username=uni_id,
                        full_name=full_name,
                        email=email,
                        role='student',
                        department=department,
                        stage=stage,
                        study_type=study_type
                    )
                    new_student.set_password(generated_password)
                    new_student.temp_password = generated_password  # حفظ كلمة المرور لعرضها للمدير
                    db.session.add(new_student)
                    success_count += 1

                except Exception as e:
                    errors.append(f"خطأ في السطر {index + 2}: {str(e)}")

            db.session.commit()
            
            if success_count > 0:
                flash(f'تم استيراد {success_count} طالب بنجاح.', 'success')
            

        except Exception as e:
            flash(f'حدث خطأ أثناء معالجة الملف: {str(e)}', 'danger')
    else:
        flash('الرجاء رفع ملف Excel بصيغة .xlsx أو .xls', 'danger')

    return redirect(url_for('main.system_administrator', active_tab='users'))
