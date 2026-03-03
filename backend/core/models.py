from django.contrib.auth.models import AbstractUser
from django.db import models
from pgvector.django import VectorField


class User(AbstractUser):
    """
    Custom User Model para ProjectOuvidoria
    Extende o modelo padrão do Django para suportar funcionalidades SaaS
    """
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True, db_index=True, verbose_name='CPF')
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome Completo')
    is_temporary = models.BooleanField(default=False, verbose_name='Usuário Temporário', help_text='Usuário criado automaticamente sem senha')
    is_active = models.BooleanField(default=True)
    
    # Setor de trabalho (para controle de acesso no Board de Execução)
    SECTOR_CHOICES = [
        ('OBRAS', 'OBRAS'),
        ('SAUDE', 'SAÚDE'),
        ('ZELADORIA', 'ZELADORIA'),
        ('TRANSPORTE', 'TRANSPORTE'),
        ('EDUCACAO', 'EDUCAÇÃO'),
        ('SEGURANCA', 'SEGURANÇA'),
        ('MEIO_AMBIENTE', 'MEIO AMBIENTE'),
        ('ILUMINACAO', 'ILUMINAÇÃO'),
    ]
    sector = models.CharField(
        max_length=50,
        choices=SECTOR_CHOICES,
        blank=True,
        null=True,
        verbose_name='Setor',
        help_text='Setor de trabalho do usuário (para controle de acesso no Board de Execução)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        if self.full_name:
            return f"{self.full_name} ({self.email or self.cpf or self.username})"
        return self.email or self.cpf or self.username

    def get_full_name(self):
        """Retorna o nome completo do usuário"""
        return self.full_name or super().get_full_name() or self.username


class TesteVetorial(models.Model):
    """
    Modelo de teste para busca vetorial com pgvector usando embeddings do Google Gemini API.
    Usa 3072 dimensões (dimensão retornada pelo modelo models/gemini-embedding-001).
    O campo embedding é gerado automaticamente via signal quando o registro é salvo.
    """
    nome = models.CharField(max_length=200, verbose_name='Nome')
    embedding = VectorField(dimensions=3072, null=True, blank=True, verbose_name='Embedding Vetorial', help_text='Gerado automaticamente via signal')

    class Meta:
        db_table = 'teste_vetorial'
        verbose_name = 'Teste Vetorial'
        verbose_name_plural = 'Testes Vetoriais'
        ordering = ['nome']

    def __str__(self):
        return self.nome
    
    def get_embedding_dimensions(self):
        """
        Retorna o número de dimensões do embedding de forma segura.
        Lida com arrays numpy retornados pelo VectorField.
        """
        if self.embedding is None:
            return 0
        try:
            import numpy as np
            if isinstance(self.embedding, np.ndarray):
                return self.embedding.size
            return len(self.embedding)
        except (TypeError, AttributeError, ImportError):
            try:
                return len(self.embedding)
            except (TypeError, AttributeError):
                return 0
    
    def has_embedding(self):
        """
        Verifica se o registro possui embedding de forma segura.
        """
        return self.embedding is not None and self.get_embedding_dimensions() > 0
