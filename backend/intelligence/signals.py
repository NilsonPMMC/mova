import threading
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from reports.models import Manifestation
from .services import LLMService

logger = logging.getLogger(__name__)


def analyze_manifestation_async(manifestation_instance):
    """
    Função auxiliar para executar análise de IA em thread separada
    Após análise, vincula automaticamente a categoria sugerida se não houver categoria manual
    """
    try:
        logger.info(f"Iniciando análise assíncrona para manifestação {manifestation_instance.protocol}")
        nlp_analysis = LLMService.analyze_manifestation(manifestation_instance)
        # Roteamento automático (auto-dispatch) é feito dentro de LLMService ao final da análise
    except Exception as e:
        logger.error(
            f"Erro na análise assíncrona da manifestação {manifestation_instance.protocol}: {str(e)}",
            exc_info=True
        )


@receiver(post_save, sender=Manifestation)
def trigger_nlp_analysis(sender, instance, created, **kwargs):
    """
    Signal que dispara análise de NLP quando uma nova manifestação é criada
    
    Para não travar o request HTTP, a análise é executada em uma thread separada
    """
    if created:
        logger.info(
            f"Nova manifestação criada: {instance.protocol}. "
            f"Disparando análise de IA em thread separada."
        )
        
        # Executar análise em thread separada para não travar o request
        thread = threading.Thread(
            target=analyze_manifestation_async,
            args=(instance,),
            daemon=True  # Thread daemon não impede o programa de encerrar
        )
        thread.start()
        
        logger.debug(f"Thread de análise iniciada para manifestação {instance.protocol}")
