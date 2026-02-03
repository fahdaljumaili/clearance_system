# app/utils/push_notifications.py
# أدوات مساعدة لإرسال إشعارات الويب الفورية (Web Push Notifications)

import json
from pywebpush import webpush, WebPushException
from flask import current_app

def send_push_to_subscription(sub_info: dict, payload: dict):
    """
    يرسل إشعار فوري (Push Notification) إلى اشتراك مستخدم واحد باستخدام مكتبة pywebpush.
    
    المعاملات:
    sub_info (dict): معلومات الاشتراك (endpoint, keys) المخزنة في قاعدة البيانات.
    payload (dict): البيانات المراد إرسالها (العنوان، المحتوى، أيقونة، رابط..).
    """
    try:
        # إرسال الإشعار باستخدام مفاتيح VAPID
        webpush(
            subscription_info=sub_info,
            data=json.dumps(payload),
            vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
            vapid_claims={"sub": current_app.config['VAPID_EMAIL']}
        )
        return True

    except WebPushException as ex:
        # التعامل مع أخطاء بروتوكول WebPush وتوثيقها
        print(f"!!! فشل إرسال الإشعار (WebPushException): {repr(ex)}")
        current_app.logger.error(f"فشل إرسال الإشعار: {repr(ex)}")
        return False
    
    except Exception as e:
        # التعامل مع أي أخطاء أخرى غير متوقعة
        print(f"!!! حدث خطأ عام غير متوقع: {repr(e)}")
        return False