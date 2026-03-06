from django.contrib import admin
from .models import NLPAnalysis


@admin.register(NLPAnalysis)
class NLPAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        'manifestation',
        'sentiment_score',
        'urgency_level',
        'intent',
        'suggested_category',
        'has_summary',
        'has_keywords',
        'ai_model_used',
        'analyzed_at',
    )
    list_filter = ('urgency_level', 'intent', 'ai_model_used', 'analyzed_at', 'suggested_category')
    search_fields = ('manifestation__protocol', 'summary', 'keywords')
    readonly_fields = ('created_at', 'updated_at', 'analyzed_at')
    fieldsets = (
        ('Manifestação', {
            'fields': ('manifestation',)
        }),
        ('Campos consumidos pela IA', {
            'description': 'Dados extraídos e preenchidos automaticamente pela análise de IA.',
            'fields': (
                'sentiment_score',
                'urgency_level',
                'intent',
                'suggested_category',
                'summary',
                'keywords',
            )
        }),
        ('Metadados da IA', {
            'fields': ('ai_model_used', 'analysis_version', 'raw_ai_response')
        }),
        ('Datas', {
            'fields': ('analyzed_at', 'created_at', 'updated_at')
        }),
    )

    def has_summary(self, obj):
        return bool(obj.summary and obj.summary.strip())
    has_summary.boolean = True
    has_summary.short_description = 'Resumo'

    def has_keywords(self, obj):
        return bool(obj.keywords and len(obj.keywords) > 0)
    has_keywords.boolean = True
    has_keywords.short_description = 'Palavras-chave'
