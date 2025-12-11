from django.apps import AppConfig

class AppRifasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_rifas'

    def ready(self):
        import app_rifas.signals

