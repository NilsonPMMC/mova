"""
Serviço de geração de embeddings usando OpenAI API.
Arquitetura 100% baseada em API - sem dependências locais pesadas.
"""
import logging
import os
from typing import List
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

# Modelo de embedding da OpenAI
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 1536  # Dimensão fixa do modelo text-embedding-3-small


class VectorService:
    """
    Serviço para gerar embeddings usando OpenAI API.
    Usa um cliente OpenAI dedicado que aponta para a URL oficial da OpenAI,
    ignorando qualquer configuração global da Groq.
    """
    
    def __init__(self):
        """
        Inicializa o cliente OpenAI apontando para a URL oficial.
        Lê a chave da variável de ambiente REAL_OPENAI_API_KEY.
        """
        api_key = os.getenv('REAL_OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError(
                "REAL_OPENAI_API_KEY não encontrada nas variáveis de ambiente. "
                "Configure esta variável no arquivo .env"
            )
        
        # Cliente OpenAI dedicado apontando para a URL oficial
        # Ignora qualquer configuração global (como OPENAI_API_BASE da Groq)
        self.client = OpenAI(
            api_key=api_key,
            base_url='https://api.openai.com/v1'  # URL oficial da OpenAI
        )
        logger.info("VectorService inicializado com OpenAI API oficial")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para um texto usando OpenAI API.
        
        Args:
            text: Texto para gerar o embedding
            
        Returns:
            Lista de floats representando o vetor de embedding (1536 dimensões)
            
        Raises:
            Exception: Se houver erro na chamada da API
        """
        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")
        
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text.strip()
            )
            
            embedding = response.data[0].embedding
            
            # Validação: garantir que temos exatamente 1536 dimensões
            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Embedding retornado tem {len(embedding)} dimensões, "
                    f"esperado {EMBEDDING_DIMENSIONS}"
                )
            
            # Log de uso (tokens usados)
            usage = response.usage
            logger.info(
                f"Embedding gerado: {usage.total_tokens} tokens "
                f"(prompt: {usage.prompt_tokens})"
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise
    
    @staticmethod
    def get_dimensions() -> int:
        """
        Retorna o número de dimensões do embedding.
        
        Returns:
            Número de dimensões (1536 para text-embedding-3-small)
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
