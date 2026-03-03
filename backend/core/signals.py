"""
Signals para automatizar a geração de embeddings no modelo TesteVetorial.
Gera automaticamente o embedding quando um registro é salvo sem vetor.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TesteVetorial
from .services.vector_service import VectorService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TesteVetorial)
def generate_embedding_on_save(sender, instance, created, **kwargs):
    """
    Signal que gera automaticamente o embedding quando um TesteVetorial é salvo.
    
    Lógica:
    - Se o registro não tem embedding (ou está vazio), gera usando o campo 'nome'
    - Usa update_fields=['embedding'] para evitar loops infinitos de post_save
    """
    # Verificar se o embedding está vazio ou None
    # VectorField retorna None ou um array numpy quando lido do banco
    # Precisamos verificar de forma segura para arrays numpy
    has_embedding = False
    if instance.embedding is not None:
        try:
            # Tentar converter para lista/array e verificar tamanho
            import numpy as np
            if isinstance(instance.embedding, np.ndarray):
                has_embedding = instance.embedding.size > 0
            else:
                has_embedding = len(instance.embedding) > 0
        except (TypeError, AttributeError, ImportError):
            # Se não conseguir verificar, assume que tem embedding se não é None
            has_embedding = True
    
    if has_embedding:
        logger.debug(
            f"TesteVetorial ID {instance.id} já possui embedding. Pulando geração automática."
        )
        return
    
    # Verificar se temos texto para gerar embedding
    if not instance.nome or not instance.nome.strip():
        logger.warning(
            f"TesteVetorial ID {instance.id} não tem texto ('nome') para gerar embedding."
        )
        return
    
    try:
        # Inicializar o serviço de vetores
        vector_service = VectorService()
        
        # Gerar embedding usando o campo 'nome' como texto
        logger.info(
            f"Gerando embedding automaticamente para TesteVetorial ID {instance.id}: '{instance.nome}'"
        )
        embedding = vector_service.get_embedding(instance.nome)
        
        # Atualizar o registro usando update_fields para evitar loop infinito
        # Usamos update() para não disparar post_save novamente
        TesteVetorial.objects.filter(pk=instance.pk).update(embedding=embedding)
        
        logger.info(
            f"Embedding gerado e salvo com sucesso para TesteVetorial ID {instance.id} "
            f"({len(embedding)} dimensões)"
        )
        
    except Exception as e:
        logger.error(
            f"Erro ao gerar embedding automaticamente para TesteVetorial ID {instance.id}: {str(e)}",
            exc_info=True
        )
        # Não relançar a exceção para não quebrar o save do modelo
        # O registro será salvo sem embedding, que pode ser gerado manualmente depois
