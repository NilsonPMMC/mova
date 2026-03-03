"""
Serviço de geração de embeddings usando o Gabinete AI Kernel (API compatível com OpenAI).
Arquitetura 100% baseada em API on-premise.
"""
import logging
from typing import List

import requests
from django.conf import settings
from requests import RequestException

logger = logging.getLogger(__name__)

# Dimensão padrão dos vetores retornados pelo Kernel (ajuste conforme contrato da API)
EMBEDDING_DIMENSIONS = 1024


class VectorService:
    """
    Serviço para gerar embeddings usando o Gabinete AI Kernel.
    Faz POST para /embeddings no servidor FastAPI on-premise, com payload
    compatível com o padrão OpenAI.
    """

    def __init__(self) -> None:
        """
        Inicializa o serviço lendo as configurações do Django:
        - AI_KERNEL_URL: URL base do Kernel (ex.: http://192.168.10.50:8004)
        - AI_KERNEL_EMBEDDING_MODEL: nome do modelo de embedding a ser utilizado
        """
        base_url = getattr(settings, "AI_KERNEL_URL", "").strip().rstrip("/")
        model = getattr(settings, "AI_KERNEL_EMBEDDING_MODEL", "").strip()

        if not base_url or not model:
            raise ValueError(
                "Configurações do AI Kernel inválidas. "
                "Defina AI_KERNEL_URL e AI_KERNEL_EMBEDDING_MODEL no .env/backend."
            )

        self.base_url = base_url
        self.model = model

        logger.info(
            "VectorService inicializado com Gabinete AI Kernel, url=%s, model=%s",
            self.base_url,
            self.model,
        )

    def get_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para um texto usando o Gabinete AI Kernel.

        Args:
            text: Texto para gerar o embedding.

        Returns:
            Lista de floats representando o vetor de embedding (tipicamente 1024 dimensões).

        Raises:
            Exception: Se houver erro na chamada da API ou na estrutura da resposta.
        """
        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")

        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model,
            "input": text.strip(),
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            embedding = data["data"][0]["embedding"]

            if not isinstance(embedding, list):
                raise ValueError("Resposta do AI Kernel não contém uma lista de embedding válida")

            # Normalizar para lista de floats
            embedding = [float(x) for x in embedding]

            if len(embedding) != EMBEDDING_DIMENSIONS:
                logger.warning(
                    "Embedding retornado tem %s dimensões, esperado %s. "
                    "Prosseguindo com a dimensão retornada.",
                    len(embedding),
                    EMBEDDING_DIMENSIONS,
                )

            logger.info(
                "Embedding gerado com sucesso (%s dimensões) para texto: '%s...'",
                len(embedding),
                text[:50].replace("\n", " "),
            )

            return embedding

        except RequestException as e:
            logger.error(
                "Erro de rede ao chamar o Gabinete AI Kernel para embeddings: %s",
                e,
                exc_info=True,
            )
            raise
        except (KeyError, IndexError, TypeError, ValueError) as e:
            body_preview = ""
            try:
                body_preview = response.text[:500]  # type: ignore[name-defined]
            except Exception:
                pass
            logger.error(
                "Resposta inválida do Gabinete AI Kernel ao gerar embedding: %s. "
                "Trecho da resposta: %s",
                e,
                body_preview,
            )
            raise

    @staticmethod
    def get_dimensions() -> int:
        """
        Retorna o número esperado de dimensões do embedding.
        """
        return EMBEDDING_DIMENSIONS

    @staticmethod
    def get_model_name() -> str:
        """
        Retorna o nome do modelo configurado para embeddings.
        """
        return getattr(settings, "AI_KERNEL_EMBEDDING_MODEL", "")
