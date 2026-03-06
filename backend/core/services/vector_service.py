import logging
import requests
from typing import List
from django.conf import settings

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        self.base_url = getattr(settings, 'AI_KERNEL_URL', 'http://192.168.10.50:8004/v1')
        self.model = getattr(settings, 'AI_KERNEL_EMBEDDING_MODEL', 'mxbai-embed-large')
        # Ollama usa /api/embed (não /v1/embeddings) e parâmetro "input"
        self._is_ollama = '11434' in self.base_url or 'ollama' in self.base_url.lower()
        logger.info(f"VectorService conectado ao Kernel: {self.base_url} (Ollama={self._is_ollama})")
    
    def get_embedding(self, text: str) -> List[float]:
        try:
            if self._is_ollama:
                # Ollama: POST /api/embed com {"model", "input"} (não usa /v1/embeddings)
                host = self.base_url.split('/v1')[0].rstrip('/') if '/v1' in self.base_url else self.base_url.rstrip('/').split('/api')[0].rstrip('/')
                url = f"{host}/api/embed"
                payload = {"model": self.model, "input": (text or '').strip() or ' '}
            else:
                # Gabinete AI Kernel: POST /v1/embeddings com {"model", "texts"}
                url = f"{self.base_url}/embeddings"
                input_key = getattr(settings, 'AI_KERNEL_EMBEDDING_INPUT_KEY', 'texts')
                texts = [text.strip()] if text else ['']
                payload = {"model": self.model, input_key: texts[0] if input_key == 'input' else texts}
            
            response = requests.post(url, json=payload, timeout=15)
            if not response.ok:
                logger.error(f"Embeddings {response.status_code}: URL={url} response={response.text[:300]}")
            response.raise_for_status()
            
            data = response.json()
            # Ollama e Gabinete AI Kernel: {"embeddings": [[...]]}
            if 'embeddings' in data:
                embedding = data['embeddings'][0]
            elif 'data' in data:
                embedding = data['data'][0].get('embedding')  # Formato OpenAI
            else:
                raise ValueError(f"Resposta sem embeddings: {list(data.keys())}")
            
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
