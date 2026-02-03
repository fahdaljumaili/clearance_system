# forms.py
# نماذج Flask-WTF للتعامل مع النماذج الإلكترونية في التطبيق
# تشمل تسجيل الدخول، إنشاء الحسابات، وطلبات براءة الذمة

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError

# نموذج تسجيل الدخول
# يستخدم للتحقق من هوية المستخدم (طالب، موظف، أو مدير)
class LoginForm(FlaskForm):
    identifier = StringField(
        'الرقم الجامعي أو اسم المستخدم',
        validators=[DataRequired(), Length(min=3, max=50)]
    )
    password = PasswordField(
        'كلمة المرور',
        validators=[DataRequired(), Length(min=6)]
    )
    submit = SubmitField('تسجيل الدخول')

# نموذج طلب براءة الذمة
# نموذج بسيط زر واحد لتقديم الطلب
class ClearanceRequestForm(FlaskForm):
    submit = SubmitField('تقديم طلب براءة الذمة')

# نموذج تحديث حالة الطلب
# يستخدمه مسؤول القسم لتغيير حالة الطالب (موافقة/رفض) وإضافة ملاحظات
class UpdateStatusForm(FlaskForm):
    status = StringField('الحالة الجديدة', validators=[DataRequired()])
    comment = StringField('ملاحظة', validators=[Length(max=200)])
    submit = SubmitField('تحديث الحالة')

# نموذج طلب استعادة كلمة المرور
# يطلب البريد الإلكتروني لإرسال رابط إعادة التعيين
class RequestResetForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    submit = SubmitField('طلب استعادة كلمة المرور')

# نموذج تعيين كلمة المرور الجديدة
# يستخدم بعد الضغط على رابط الاستعادة
class ResetPasswordForm(FlaskForm):
    password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired()])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('تغيير كلمة المرور')

# نموذج إضافة مستخدم جديد (مستخدم من قبل مدير النظام)
# يدعم إضافة جميع أنواع المستخدمين مع حقول ديناميكية حسب الدور
class AddUserForm(FlaskForm):
    role = SelectField('نوع الحساب', choices=[('student', 'طالب'), ('department_officer', 'مسؤول القسم'), ('system_admin', 'مدير النظام')], validators=[DataRequired()])
    full_name = StringField('الاسم الكامل')
    username = StringField('اسم المستخدم', validators=[Optional(), Length(min=3, max=50)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    
    # حقول إضافية اختيارية حسب النوع
    university_id = StringField('الرقم الجامعي')
    department = StringField('القسم')
    stage = StringField('المرحلة')
    study_type = StringField('نوع الدراسة')
    submit = SubmitField('إضافة المستخدم')

    # التحقق من عدم تكرار البريد الإلكتروني
    def validate_email(self, email):
        from app.models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني مسجل بالفعل. يرجى استخدام بريد آخر.')

    # التحقق من عدم تكرار اسم المستخدم وتوفره للموظفين
    def validate_username(self, username):
        if self.role.data != 'student' and not username.data:
            raise ValidationError('اسم المستخدم مطلوب للموظفين والمشرفين.')
            
        if username.data:
            from app.models import User
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('اسم المستخدم مسجل بالفعل. يرجى اختيار اسم آخر.')
    
    # التحقق من وجود الاسم الكامل للطلاب
    def validate_full_name(self, full_name):
        if self.role.data == 'student' and not full_name.data:
            raise ValidationError('اسم الطالب مطلوب.')

# نموذج تعديل بيانات المستخدم
# مشابه لنموذج الإضافة لكن بدون التحقق الصارم من كلمة المرور (لأنها اختيارية عند التعديل)
class EditUserForm(FlaskForm):
    role = SelectField('نوع الحساب', choices=[('student', 'طالب'), ('department_officer', 'مسؤول القسم'), ('system_admin', 'مدير النظام')], validators=[DataRequired()])
    full_name = StringField('الاسم الكامل')
    username = StringField('اسم المستخدم', validators=[Optional(), Length(min=3, max=50)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[Optional(), Length(min=6)])
    # حقول إضافية
    university_id = StringField('الرقم الجامعي')
    department = StringField('القسم')
    stage = StringField('المرحلة')
    study_type = StringField('نوع الدراسة')
    submit = SubmitField('حفظ التغييرات')
