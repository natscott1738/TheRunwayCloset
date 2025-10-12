from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'


    def ready(self):
        # import signals so they register
        from . import signals  # noqa: F401
