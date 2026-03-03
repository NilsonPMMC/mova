from django.contrib import admin
from .models import NLPAnalysis


@admin.register(NLPAnalysis)
class NLPAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        'manifestation',
        'sentiment_score',
        'urgency_level',
        'suggested_category',
        'ai_model_used',
        'analyzed_at'
    )
    list_filter = ('urgency_level', 'ai_model_used', 'analyzed_at', 'suggested_category')
    search_fields = ('manifestation__protocol', 'summary', 'keywords')
    readonly_fields = ('created_at', 'updated_at', 'analyzed_at')
    fieldsets = (
        ('Manifestação', {
            'fields': ('manifestation',)
        }),
        ('Análise de Sentimento', {
            'fields': ('sentiment_score',)
        }),
        ('Urgência e Classificação', {
            'fields': ('urgency_level', 'suggested_category')
        }),
        ('Extração de Informações', {
            'fields': ('keywords', 'summary')
        }),
        ('Metadados da IA', {
            'fields': ('ai_model_used', 'analysis_version', 'raw_ai_response')
        }),
        ('Datas', {
            'fields': ('analyzed_at', 'created_at', 'updated_at')
        }),
    )
