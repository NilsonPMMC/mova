import logging
import threading
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Manifestation, ManifestationUpdate
from core.services.vector_service import VectorService

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Manifestation)
def generate_protocol_if_needed(sender, instance, **kwargs):
    """
    Signal para garantir que o protocolo seja gerado automaticamente
    antes de salvar a manifestação, mesmo em operações bulk.
    """
    if not instance.protocol:
        # Garantir unicidade do protocolo
        while True:
            protocol = instance.generate_protocol()
            if not Manifestation.objects.filter(protocol=protocol).exists():
                instance.protocol = protocol
                break


def _run_deduplication_async(manifestation_id):
    """Executa detecção de duplicidade após breve delay (para IA definir categoria)."""
    import time
    from reports.models import Manifestation
    from intelligence.services import DeduplicationService
    time.sleep(5)
    try:
        manifestation = Manifestation.objects.filter(pk=manifestation_id).select_related('category', 'nlp_analysis').first()
        if manifestation and (manifestation.latitude is not None and manifestation.longitude is not None):
            DeduplicationService.detect_duplicates(manifestation)
    except Exception as e:
        logger.warning("Deduplicação assíncrona falhou: %s", e)


@receiver(post_save, sender=Manifestation)
def trigger_deduplication(sender, instance, created, **kwargs):
    """
    Após criar uma manifestação com localização, dispara detecção de duplicidade
    em thread (com delay para a IA eventualmente definir a categoria).
    """
    if created and instance.latitude is not None and instance.longitude is not None:
        threading.Thread(target=_run_deduplication_async, args=(instance.pk,), daemon=True).start()


@receiver(post_save, sender=ManifestationUpdate)
def update_manifestation_status(sender, instance, created, **kwargs):
    """
    Signal para atualizar automaticamente o status da manifestação
    quando um novo andamento é criado
    """
    if created and instance.new_status:
        manifestation = instance.manifestation
        # Atualizar status apenas se for diferente do atual
        if manifestation.status != instance.new_status:
            manifestation.status = instance.new_status
            # Se foi resolvida, registrar data de resolução
            if instance.new_status == Manifestation.STATUS_RESOLVED and not manifestation.resolved_at:
                from django.utils import timezone
                manifestation.resolved_at = timezone.now()
                # Se houver usuário autenticado no contexto, associar resolved_by
                if instance.updated_by:
                    manifestation.resolved_by = instance.updated_by
            manifestation.save(update_fields=['status', 'resolved_at', 'resolved_by'])


@receiver(post_save, sender=Manifestation)
def generate_embedding_for_manifestation(sender, instance, created, **kwargs):
    """
    Signal que gera automaticamente o embedding quando uma Manifestation é salva.
    
    Lógica:
    - Se é criação (created=True) ou se a descrição foi alterada, gera embedding
    - Usa o campo 'description' como texto para gerar o vetor
    - Atualiza usando update() para evitar loop infinito de post_save
    """
    # Verificar se temos descrição para gerar embedding
    if not instance.description or not instance.description.strip():
        logger.debug(
            f"Manifestation {instance.protocol} não tem descrição. Pulando geração de embedding."
        )
        return
    
    # Verificar se já tem embedding (evitar regenerar desnecessariamente)
    has_embedding = False
    if instance.embedding is not None:
        try:
            import numpy as np
            if isinstance(instance.embedding, np.ndarray):
                has_embedding = instance.embedding.size > 0
            else:
                has_embedding = len(instance.embedding) > 0
        except (TypeError, AttributeError, ImportError):
            # Se não conseguir verificar, assume que tem embedding se não é None
            has_embedding = True
    
    # Se já tem embedding e não é criação, verificar se a descrição mudou
    if has_embedding and not created:
        # Verificar se a descrição foi alterada comparando com o banco
        try:
            old_instance = Manifestation.objects.get(pk=instance.pk)
            if old_instance.description == instance.description:
                logger.debug(
                    f"Manifestation {instance.protocol} já tem embedding e descrição não mudou. "
                    "Pulando geração automática."
                )
                return
        except Manifestation.DoesNotExist:
            pass  # Se não existe no banco, continua para gerar
    
    # Gerar embedding em thread separada para não bloquear o save
    def _generate_embedding_async(manifestation_id, description_text):
        """Gera embedding de forma assíncrona"""
        try:
            vector_service = VectorService()
            logger.info(
                f"Gerando embedding automaticamente para Manifestation ID {manifestation_id}: "
                f"'{description_text[:50]}...'"
            )
            embedding = vector_service.get_embedding(description_text)
            
            # Atualizar usando update() para não disparar post_save novamente
            Manifestation.objects.filter(pk=manifestation_id).update(embedding=embedding)
            
            logger.info(
                f"Embedding gerado e salvo com sucesso para Manifestation ID {manifestation_id} "
                f"({len(embedding)} dimensões)"
            )
        except Exception as e:
            logger.error(
                f"Erro ao gerar embedding automaticamente para Manifestation ID {manifestation_id}: {str(e)}",
                exc_info=True
            )
            # Não relançar a exceção - o registro será salvo sem embedding
    
    # Executar em thread separada para não bloquear o save
    threading.Thread(
        target=_generate_embedding_async,
        args=(instance.pk, instance.description),
        daemon=True
    ).start()
