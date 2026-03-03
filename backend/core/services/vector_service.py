"""
Serviço de geração de embeddings usando Google Gemini API.
Arquitetura 100% baseada em API - leve e gratuito.
Usa o novo pacote google-genai (substituiu google-generativeai).
"""
import logging
import os
from typing import List
import requests

logger = logging.getLogger(__name__)

# Modelo de embedding do Google Gemini (nome aceito pela API)
EMBEDDING_MODEL = 'models/gemini-embedding-001'
EMBEDDING_DIMENSIONS = 3072  # Dimensão retornada pelo modelo gemini-embedding-001


def _list_embedding_models(api_key: str) -> None:
    """
    Debug: lista no console os modelos disponíveis para esta chave de API
    que suportam embedContent, para facilitar diagnóstico.
    """
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        r = requests.get(url, params={"key": api_key}, timeout=10)
        r.raise_for_status()
        data = r.json()
        models = data.get("models") or []
        embedding_models = [
            m.get("name", "")
            for m in models
            if "embedContent" in (m.get("supportedGenerationMethods") or [])
        ]
        logger.info(
            "Modelos de embedding disponíveis para esta API key: %s",
            embedding_models or "(nenhum encontrado)",
        )
        if not embedding_models:
            all_names = [m.get("name", "") for m in models[:20]]
            logger.info("Primeiros modelos listados (amostra): %s", all_names)
    except Exception as e:
        logger.warning("Não foi possível listar modelos (debug): %s", e)


class VectorService:
    """
    Serviço para gerar embeddings usando Google Gemini API.
    Usa o modelo models/gemini-embedding-001 (nome aceito pela API) com 3072 dimensões.
    Usa a API REST diretamente para maior compatibilidade.
    """
    
    def __init__(self):
        """
        Inicializa o serviço.
        Lê a chave da variável de ambiente GEMINI_API_KEY.
        """
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY não encontrada nas variáveis de ambiente. "
                "Configure esta variável no arquivo .env. "
                "Obtenha sua chave em: https://makersuite.google.com/app/apikey"
            )
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        logger.info(
            "VectorService inicializado com Google Gemini API (REST), modelo=%s",
            EMBEDDING_MODEL,
        )
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para um texto usando Google Gemini API REST.
        
        Args:
            text: Texto para gerar o embedding
            
        Returns:
            Lista de floats representando o vetor de embedding (3072 dimensões)
            
        Raises:
            Exception: Se houver erro na chamada da API
        """
        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")
        
        try:
            # URL e nome do modelo (evitar duplicar "models/" se já presente)
            model_name = EMBEDDING_MODEL if EMBEDDING_MODEL.startswith("models/") else f"models/{EMBEDDING_MODEL}"
            url = f"{self.base_url}/{model_name}:embedContent"
            # Payload da requisição
            payload = {
                "model": model_name,
                "content": {
                    "parts": [{"text": text.strip()}]
                },
            }
            
            # Headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Parâmetros da query (API key)
            params = {
                "key": self.api_key
            }
            
            # Fazer requisição
            response = requests.post(url, json=payload, headers=headers, params=params)
            response.raise_for_status()
            
            # Processar resposta
            data = response.json()
            
            # Extrair embedding da resposta
            embedding_data = data.get('embedding', {})
            embedding = embedding_data.get('values', [])
            
            if not embedding:
                raise ValueError("Resposta da API não contém embedding válido")
            
            # Converter para lista de floats
            embedding = [float(x) for x in embedding]
            
            # Validação: verificar dimensões
            if len(embedding) != EMBEDDING_DIMENSIONS:
                logger.warning(
                    f"Embedding retornado tem {len(embedding)} dimensões, "
                    f"esperado {EMBEDDING_DIMENSIONS}. Usando dimensão retornada."
                )
                # Atualizar dimensões esperadas se necessário
                # (alguns modelos podem retornar dimensões diferentes)
            
            logger.info(
                f"Embedding gerado com sucesso para texto: '{text[:50]}...' "
                f"({len(embedding)} dimensões)"
            )
            
            return embedding
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro HTTP ao gerar embedding: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text[:200]}"
            logger.error(error_msg)
            # Debug: listar modelos disponíveis para esta API key (ex.: 404 = modelo não encontrado)
            if e.response.status_code == 404:
                _list_embedding_models(self.api_key)
            raise Exception(error_msg) from e
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise
    
    @staticmethod
    def get_dimensions() -> int:
        """
        Retorna o número de dimensões do embedding.
        
        Returns:
            Número de dimensões (3072 para gemini-embedding-001)
        """
        return EMBEDDING_DIMENSIONS
    
    @staticmethod
    def get_model_name() -> str:
        """
        Retorna o nome do modelo usado.
        
        Returns:
            Nome do modelo de embedding
        """
        return EMBEDDING_MODEL
