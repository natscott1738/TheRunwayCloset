import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from utils.validators import validate_e164_phone

class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, validators=[validate_e164_phone])
    ROLE_CHOICES = [
            ('admin','admin'),
            ('seller','seller'),
            ('customer','customer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    REQUIRED_FIELDS = ['email']
    def __str__(self): return self.username or str(self.email)
