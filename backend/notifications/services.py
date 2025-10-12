# notifications/services.py
from .models import Notification
from django.conf import settings

# optional: import tasks if celery is configured
try:
    from .tasks import send_email_task, send_sms_task
except Exception:
    send_email_task = None
    send_sms_task = None

def create_and_dispatch_notification(user, title, body, data=None, channels=None, notif_type="system"):
    """
    Create notifications (in-db) and dispatch to channels.
    channels: list containing any of ['in_app','email','sms']
    """
    data = data or {}
    channels = channels or ["in_app"]
    created = []

    if "in_app" in channels:
        n = Notification.objects.create(user=user, type=notif_type, title=title, body=body, data=data, channel="in_app")
        created.append(n)

    if "email" in channels and getattr(user, "email", None):
        Notification.objects.create(user=user, type=notif_type, title=title, body=body, data=data, channel="email", delivered=False)
        if send_email_task:
            try:
                send_email_task.delay(user.id, title, body, data)
            except Exception:
                # fallback: ignore
                pass
        else:
            # quick sync fallback using Django send_mail (non-blocking not ensured)
            try:
                from django.core.mail import send_mail
                send_mail(title, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
            except Exception:
                pass

    if "sms" in channels and getattr(user, "phone_number", None):
        Notification.objects.create(user=user, type=notif_type, title=title, body=body, data=data, channel="sms", delivered=False)
        if send_sms_task:
            try:
                send_sms_task.delay(user.id, body, data)
            except Exception:
                pass
        else:
            # implement direct SMS send if you wish
            pass

    return created
