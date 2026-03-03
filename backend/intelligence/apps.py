from django.apps import AppConfig


class IntelligenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'intelligence'
    verbose_name = 'Intelligence'

    def ready(self):
        """Importa os signals quando o app estiver pronto"""
        import intelligence.signals  # noqa
