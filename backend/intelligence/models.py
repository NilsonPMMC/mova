from django.db import models
from reports.models import Manifestation, ManifestationCategory
from utils.models import TimeStampedModel


class NLPAnalysis(TimeStampedModel):
    """
    Modelo para armazenar análises de NLP/IA das manifestações.
    Este é o "cérebro" da operação, armazenando todas as análises de IA.
    """
    manifestation = models.OneToOneField(
        Manifestation,
        on_delete=models.CASCADE,
        related_name='nlp_analysis',
        verbose_name='Manifestação'
    )
    
    # Análise de Sentimento
    sentiment_score = models.FloatField(
        default=0.0,
        verbose_name='Score de Sentimento',
        help_text='Valor entre -1.0 (muito negativo) e +1.0 (muito positivo)'
    )
    
    # Nível de Urgência calculado pela IA
    urgency_level = models.IntegerField(
        default=3,
        verbose_name='Nível de Urgência',
        help_text='Valor de 1 (baixa) a 5 (crítica) calculado pela IA'
    )
    
    # Sugestão de Categoria pela IA
    suggested_category = models.ForeignKey(
        ManifestationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nlp_suggestions',
        verbose_name='Categoria Sugerida'
    )
    
    # Palavras-chave extraídas
    keywords = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Palavras-chave',
        help_text='Lista de palavras-chave extraídas pela IA'
    )
    
    # Resumo gerado pela IA
    summary = models.TextField(
        blank=True,
        null=True,
        verbose_name='Resumo',
        help_text='Resumo gerado pela IA para leitura rápida do gestor'
    )
    
    # Intenção da manifestação detectada pela IA
    INTENT_COMPLAINT = 'COMPLAINT'
    INTENT_SUGGESTION = 'SUGGESTION'
    INTENT_INFORMATION = 'INFORMATION'
    INTENT_DENUNCIATION = 'DENUNCIATION'
    
    INTENT_CHOICES = [
        (INTENT_COMPLAINT, 'Reclamação'),
        (INTENT_SUGGESTION, 'Sugestão'),
        (INTENT_INFORMATION, 'Dúvida/Informação'),
        (INTENT_DENUNCIATION, 'Denúncia'),
    ]
    
    intent = models.CharField(
        max_length=20,
        choices=INTENT_CHOICES,
        default=INTENT_COMPLAINT,
        verbose_name='Intenção',
        help_text='Tipo de manifestação detectada pela IA'
    )
    
    # Resposta completa da IA para auditoria
    raw_ai_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Resposta Bruta da IA',
        help_text='JSON completo retornado pela API de IA para auditoria futura'
    )
    
    # Metadados da análise
    ai_model_used = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Modelo de IA Utilizado',
        help_text='Ex: gpt-4, gpt-3.5-turbo, etc.'
    )
    analysis_version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name='Versão da Análise',
        help_text='Versão do algoritmo/pipeline de análise usado'
    )
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Análise'
    )

    class Meta:
        db_table = 'nlp_analyses'
        verbose_name = 'Análise NLP'
        verbose_name_plural = 'Análises NLP'
        ordering = ['-analyzed_at']
        indexes = [
            models.Index(fields=['sentiment_score']),
            models.Index(fields=['urgency_level']),
            models.Index(fields=['analyzed_at']),
        ]

    def __str__(self):
        return f"{self.manifestation.protocol} - Sentimento: {self.sentiment_score:.2f} - Urgência: {self.urgency_level}"

    def get_sentiment_label(self):
        """
        Retorna o label do sentimento baseado no score
        """
        if self.sentiment_score >= 0.3:
            return 'Positivo'
        elif self.sentiment_score <= -0.3:
            return 'Negativo'
        else:
            return 'Neutro'

    def get_urgency_label(self):
        """
        Retorna o label do nível de urgência
        """
        urgency_labels = {
            1: 'Muito Baixa',
            2: 'Baixa',
            3: 'Média',
            4: 'Alta',
            5: 'Crítica'
        }
        return urgency_labels.get(self.urgency_level, 'Desconhecido')

    def get_intent_display(self):
        """
        Retorna o label da intenção
        """
        return dict(self.INTENT_CHOICES).get(self.intent, 'Reclamação')
