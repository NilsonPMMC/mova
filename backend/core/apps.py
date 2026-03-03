from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'
    
    def ready(self):
        """
        Método chamado quando a aplicação está pronta.
        Importa os signals para garantir que sejam registrados.
        """
        import core.signals  # noqa: F401
