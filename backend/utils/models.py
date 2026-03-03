from django.db import models
import uuid


class TimeStampedModel(models.Model):
    """
    Modelo abstrato que fornece campos created_at e updated_at
    para todos os modelos que herdam dele.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')

    class Meta:
        abstract = True
        ordering = ['-created_at']
