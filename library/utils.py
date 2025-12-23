from datetime import timedelta
from django.utils import timezone


def get_default_due_date():
    return timezone.now().date() + timedelta(days=14)