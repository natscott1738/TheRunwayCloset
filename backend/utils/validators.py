import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.text import slugify


def validate_e164_phone(value):
    """
    Validates and normalizes phone numbers into E.164 format.
    Accepts numbers like '0791529449' or '+254791529449'.
    Always returns normalized '+254...' format.
    """
    if not value:
        return

    try:
        # Try parsing — default to Kenya if no country code is given
        phone = phonenumbers.parse(value, "KE")  
        if not phonenumbers.is_valid_number(phone):
            raise ValidationError("Invalid phone number")

        # Return normalized E.164 format
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        raise ValidationError("Invalid phone number")

def unique_slugify(instance, value, slug_field_name='slug', queryset=None):
    """
    Generates a unique slug from the given value.
    """
    slug = slugify(value)[:50] or 'item'
    Model = instance.__class__

    if queryset is None:
        queryset = Model._default_manager.all()
    base = slug
    i = 1
    while queryset.filter(**{slug_field_name: slug}).exclude(pk=instance.pk).exists():
        slug = f'{base}-{i}'
        i += 1

    setattr(instance, slug_field_name, slug)
    return slug
