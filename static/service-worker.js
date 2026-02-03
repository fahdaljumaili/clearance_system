// 
// Service Worker للإشعارات الفورية
// يعمل في الخلفية حتى لو كانت الصفحة مغلقة
//

self.addEventListener('push', event => {
  let data = {};

  // محاولة قراءة البيانات القادمة مع الإشعار
  try { data = event.data.json(); }
  catch (e) {
    // في حال فشل قراءة JSON, نستخدم كائن فارغ
    console.error('Push data parse error', e);
  }

  // تحديد العنوان والنص الافتراضي في حال عدم توفرهما
  const title = data.title || 'إشعار جديد';
  const options = {
    body: data.body || '', // محتوى الرسالة
    icon: '/static/icons/icon.png', // أيقونة الإشعار (تأكد من وجود المسار الصحيح)
    badge: '/static/icons/badge.png' // شارة صغيرة تظهر في شريط الحالة (Android)
  };

  // عرض الإشعار للمستخدم
  // event.waitUntil يضمن عدم إغلاق الـ worker قبل عرض الإشعار
  event.waitUntil(self.registration.showNotification(title, options));
});

// النقر على الإشعار (اختياري - لفتح الصفحة عند النقر)
self.addEventListener('notificationclick', function (event) {
  console.log('[Service Worker] Notification click Received.');
  event.notification.close(); // إغلاق الإشعار

  // فتح الصفحة الرئيسية أو نافذة المتصفح
  event.waitUntil(
    clients.openWindow('/')
  );
});
