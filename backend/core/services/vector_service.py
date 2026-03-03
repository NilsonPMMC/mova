import logging
import requests
from typing import List
from django.conf import settings

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        self.base_url = getattr(settings, 'AI_KERNEL_URL', 'http://192.168.10.50:8004/v1')
        self.model = getattr(settings, 'AI_KERNEL_EMBEDDING_MODEL', 'mxbai-embed-large')
        logger.info(f"VectorService conectado ao Kernel: {self.base_url}")
    
    def get_embedding(self, text: str) -> List[float]:
        try:
            url = f"{self.base_url}/embeddings"
            payload = {"model": self.model, "input": text.strip()}
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            embedding = data['data'][0]['embedding']
            
            if len(embedding) != 1024:
                logger.warning(f"Dimensão inesperada: {len(embedding)}. Esperado: 1024")
                
            return embedding
        except Exception as e:
            logger.error(f"Erro no Gabinete AI Kernel (Embeddings): {str(e)}")
            raise

    @staticmethod
    def get_dimensions() -> int:
        return 1024

    @staticmethod
    def get_model_name() -> str:
        return "mxbai-embed-large"
