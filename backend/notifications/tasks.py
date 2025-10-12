from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

@shared_task
def send_email_task(user_id, subject, body, data=None):
    try:
        user = User.objects.get(pk=user_id)
        if user.email:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    except Exception:
        import logging
        logging.exception("send_email_task failed")

@shared_task
def send_sms_task(user_id, body, data=None):
    # implement SMS sending via Daraja/Twilio; placeholder
    try:
        user = User.objects.get(pk=user_id)
        if getattr(user, "phone_number", None):
            # call your SMS client here (e.g., utils.daraja or 3rd party)
            pass
    except Exception:
        import logging
        logging.exception("send_sms_task failed")
