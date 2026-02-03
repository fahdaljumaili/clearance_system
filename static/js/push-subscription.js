document.addEventListener('DOMContentLoaded', async () => {
  // الحصول على عناصر الأزرار في الواجهة
  const enableBtn = document.getElementById('enable-notifications');
  const disableBtn = document.getElementById('disable-notifications');

  // إذا لم يكن زر التفعيل موجوداً (لسنا في صفحة الطالب أو المسؤول)، نتوقف هنا
  if (!enableBtn) return;

  // استخراج مفتاح VAPID العام من خاصية dataset في الزر
  const vapidKey = enableBtn.dataset.vapidKey;
  console.log('🔑 VAPID key:', vapidKey);

  // 1) تحقق من بروتوكول الأمان
  // المتصفحات تتطلب HTTPS أو localhost لعمل Service Workers والإشعارات
  if (!location.origin.startsWith('https') && !location.hostname.startsWith('localhost')) {
    alert('Push يحتاج HTTPS أو localhost');   // Edge لا يعتبر 127.0.0.1 آمناً في بعض الأحيان
    return;
  }

  // 2) تسجيل Service Worker (مرة واحدة عند تحميل الصفحة)
  // هذا الملف هو المسؤول عن استقبال الإشعارات في الخلفية
  const registration = await navigator.serviceWorker.register('/service-worker.js');

  // انتظار الجاهزية
  await navigator.serviceWorker.ready;
  console.log('✅ Service Worker جاهز');

  // 3) معالجة النقر على زر "تفعيل الإشعارات"
  enableBtn.addEventListener('click', async () => {
    // التحقق من حالة الإذن الحالية
    if (Notification.permission === 'default') {
      // طلب الإذن من المستخدم
      const perm = await Notification.requestPermission();
      console.log('📩 Notification.permission=', perm);
      if (perm !== 'granted') return alert('يجب السماح بالإشعارات.');
    } else if (Notification.permission === 'denied') {
      return alert('رجاءً فعّل الإشعارات من إعدادات الموقع.');
    }

    try {
      // التحقق مما إذا كان هناك اشتراك موجود بالفعل
      // لا ننشئ اشتراكاً جديداً إذا كان موجوداً لتجنب التكرار
      let sub = await registration.pushManager.getSubscription();
      if (!sub) {
        // إنشاء اشتراك جديد باستخدام المفتاح العام
        sub = await registration.pushManager.subscribe({
          userVisibleOnly: true, // الإشعارات ستكون مرئية دائماً للمستخدم
          applicationServerKey: urlBase64ToUint8Array(vapidKey)
        });
        console.log('📦 Subscription:', sub);
      } else {
        console.log('ℹ️ لديك اشتراك سابق، لن ننشئ آخر.');
      }

      // إرسال تفاصيل الاشتراك إلى الخادم (Backend) لحفظها في قاعدة البيانات
      await fetch('/save-subscription', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sub)
      });
      alert('✅ تم تفعيل الإشعارات بنجاح');

    } catch (err) {
      console.error('❌ فشل الاشتراك:', err.name, err.message);
      alert('فشل الاشتراك: ' + err.message);
    }
  });

  // 4) معالجة النقر على زر "إلغاء الإشعارات"
  disableBtn?.addEventListener('click', async () => {
    const sub = await registration.pushManager.getSubscription();
    if (!sub) return alert('🚫 لا يوجد اشتراك لإلغائه');

    // إلغاء الاشتراك من المتصفح
    await sub.unsubscribe();

    // إعلام الخادم بحذف الاشتراك من قاعدة البيانات
    await fetch('/delete-subscription', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ endpoint: sub.endpoint })
    });
    alert('✅ تم إلغاء تفعيل الإشعارات');
  });
});

// دالة مساعدة لتحويل مفتاح VAPID من صيغة Base64 إلى صيغة Uint8Array
// هذه الدالة ضرورية لأن المتصفح يحتاج المفتاح كمصفوفة ثنائية
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}
