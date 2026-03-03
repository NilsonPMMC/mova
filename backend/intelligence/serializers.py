from rest_framework import serializers
from .models import NLPAnalysis


class NLPAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer para análise NLP/IA de uma manifestação
    """
    sentiment_label = serializers.SerializerMethodField()
    urgency_label = serializers.SerializerMethodField()
    suggested_category_name = serializers.SerializerMethodField()
    intent_label = serializers.SerializerMethodField()

    class Meta:
        model = NLPAnalysis
        fields = [
            'id',
            'sentiment_score',
            'sentiment_label',
            'urgency_level',
            'urgency_label',
            'intent',
            'intent_label',
            'suggested_category',
            'suggested_category_name',
            'keywords',
            'summary',
            'ai_model_used',
            'analysis_version',
            'analyzed_at',
        ]
        read_only_fields = ['id', 'analyzed_at']

    def get_sentiment_label(self, obj):
        """Retorna o label do sentimento"""
        return obj.get_sentiment_label()

    def get_urgency_label(self, obj):
        """Retorna o label da urgência"""
        return obj.get_urgency_label()

    def get_suggested_category_name(self, obj):
        """Retorna o nome da categoria sugerida"""
        if obj.suggested_category:
            return obj.suggested_category.name
        return None

    def get_intent_label(self, obj):
        """Retorna o label da intenção"""
        return obj.get_intent_display() if hasattr(obj, 'get_intent_display') else dict(NLPAnalysis.INTENT_CHOICES).get(obj.intent, 'Reclamação')
