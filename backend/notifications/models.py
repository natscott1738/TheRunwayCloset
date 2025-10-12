from django.db import models
from django.conf import settings
import uuid
from core.models import TimeStampedModel

class Notification(TimeStampedModel):
    CHANNEL_CHOICES = [
        ("in_app","In App"),
        ("email","Email"),
        ("sms","SMS"),
        ("push","Push"),
    ]
    TYPE_CHOICES = [
        ("payment","Payment"),
        ("order","Order"),
        ("system","System"),
        ("promotion","Promotion"),
        ("review","Review"),
        ("inventory","Inventory"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True, help_text="Target user for this notification. Null for global/system notifications.")
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default="system")
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES, default="in_app")
    is_read = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["type"]),
            models.Index(fields=["channel"]),
        ]


    def __str__(self):
        return f"{self.type}: {self.title} -> {self.user or 'System'}"
