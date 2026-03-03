from django.db import models


class ExternalSystem(models.Model):
    """
    Modelo para gerenciar integrações com sistemas externos
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    api_endpoint = models.URLField()
    api_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'external_systems'
        verbose_name = 'Sistema Externo'
        verbose_name_plural = 'Sistemas Externos'

    def __str__(self):
        return self.name
