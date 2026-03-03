import json
import re
import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from requests import RequestException
from .models import NLPAnalysis
from reports.models import ManifestationCategory

logger = logging.getLogger(__name__)


class LLMService:
    """
    Serviço de triagem automática usando o Gabinete AI Kernel (FastAPI on-premise).

    Endpoint esperado do Kernel:
    - {AI_KERNEL_URL}/chat
    Payload:
      {
        "model": settings.AI_KERNEL_CHAT_MODEL,
        "system_prompt": <prompt de sistema>,
        "user_prompt": <texto do usuário>
      }
    """

    @staticmethod
    def _extract_json_with_regex(text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai o primeiro objeto JSON válido de um texto, usando regex,
        para casos em que o modelo adiciona texto antes/depois do JSON.
        """
        # Tentar diretamente primeiro
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Procurar bloco JSON principal com regex
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None

        return None

    @staticmethod
    def analyze_text(text, save_to_db: bool = False, manifestation_instance=None):
        """
        Analisa um texto usando o Gabinete AI Kernel e retorna dados estruturados.

        Args:
            text: Texto a ser analisado
            save_to_db: Se True, salva no banco (requer manifestation_instance)
            manifestation_instance: Instância de Manifestation (obrigatório se save_to_db=True)

        Returns:
            dict ou NLPAnalysis: Dados estruturados da análise ou None em caso de erro
        """
        if save_to_db and not manifestation_instance:
            raise ValueError("manifestation_instance é obrigatório quando save_to_db=True")

        try:
            api_base = getattr(settings, "AI_KERNEL_URL", "").strip().rstrip("/")
            model = getattr(settings, "AI_KERNEL_CHAT_MODEL", "").strip()

            if not api_base or not model:
                logger.warning(
                    "AI_KERNEL_URL ou AI_KERNEL_CHAT_MODEL não configurados. "
                    "Análise não será executada."
                )
                return None

            url = f"{api_base}/chat"

            system_message = """
Você é um Analista de Ouvidoria da Prefeitura. Sua tarefa é categorizar manifestações de cidadãos.

Retorne APENAS um objeto JSON válido, sem markdown, sem texto antes ou depois.

O JSON DEVE conter OBRIGATORIAMENTE estas chaves:
- category: string com o nome da categoria sugerida (ex.: "Iluminação Pública", "Buraco em Via/Pavimentação")
- urgency_level: inteiro de 1 (pouco urgente) a 5 (crítico/risco de vida)
- sentiment: float entre -1.0 (muito negativo/raiva) e 1.0 (positivo/elogio)

Você PODE opcionalmente incluir:
- summary: string com um resumo executivo em UMA frase
- keywords: array de 3 a 5 palavras-chave importantes do texto

Regras importantes:
- category deve usar nomes claros, compatíveis com categorias de Ouvidoria (ex.: "Iluminação Pública", "Buraco em Via/Pavimentação", "Saúde/Falta de Médico", "Coleta de Lixo", "Zeladoria", "Trânsito", "Segurança", "Meio Ambiente").
- urgency_level = 5 para risco de vida ou emergências graves; 1 para casos de baixa prioridade.
- sentiment negativo (perto de -1.0) para reclamações fortes/raiva, neutro (~0.0) para dúvidas, positivo (>0.0) para elogios.

IMPORTANTE:
- Responda APENAS com o JSON. NÃO inclua comentários, markdown ou texto solto.
"""

            payload = {
                "model": model,
                "system_prompt": system_message,
                "user_prompt": text,
            }

            logger.info(
                "Iniciando análise de IA via Gabinete AI Kernel (model=%s, base=%s)",
                model,
                api_base,
            )

            try:
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status()
            except RequestException as e:
                logger.error(
                    "Erro de rede ao chamar o Gabinete AI Kernel para triagem: %s",
                    e,
                    exc_info=True,
                )
                return None

            # Endpoint /v1/chat do Gabinete AI Kernel retorna diretamente uma string JSON.
            ai_response_text = response.json()

            ai_data = LLMService._extract_json_with_regex(ai_response_text)

            if not ai_data:
                logger.error(
                    "Erro ao extrair JSON da resposta do LLM. Resposta recebida: %s",
                    ai_response_text[:500],
                )
                return None

            # Mapear novas chaves obrigatórias (category, urgency_level, sentiment)
            sentiment_score = float(
                ai_data.get("sentiment", ai_data.get("sentiment_score", 0.0))
            )
            urgency_level = int(ai_data.get("urgency_level", 3))
            suggested_category_name = ai_data.get(
                "category", ai_data.get("suggested_category", "")
            )

            # Campos opcionais/legados
            summary = ai_data.get("summary", "")
            keywords = ai_data.get("keywords", [])
            intent = ai_data.get("intent", "COMPLAINT")

            # Sanitização básica
            valid_intents = ["COMPLAINT", "SUGGESTION", "INFORMATION", "DENUNCIATION"]
            if intent not in valid_intents:
                intent = "COMPLAINT"

            if not isinstance(keywords, list):
                keywords = []

            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            urgency_level = max(1, min(5, urgency_level))

            # Resolver categoria no banco
            suggested_category = None
            if suggested_category_name:
                suggested_category_name = suggested_category_name.strip()

                category_mapping = {
                    "iluminação pública": "Iluminação Pública",
                    "iluminacao publica": "Iluminação Pública",
                    "luz": "Iluminação Pública",
                    "poste": "Iluminação Pública",
                    "lâmpada": "Iluminação Pública",
                    "lampada": "Iluminação Pública",
                    "buraco": "Buraco em Via/Pavimentação",
                    "pavimentação": "Buraco em Via/Pavimentação",
                    "pavimentacao": "Buraco em Via/Pavimentação",
                    "rua": "Buraco em Via/Pavimentação",
                    "calçada": "Buraco em Via/Pavimentação",
                    "calcada": "Buraco em Via/Pavimentação",
                    "saúde": "Saúde/Falta de Médico",
                    "saude": "Saúde/Falta de Médico",
                    "médico": "Saúde/Falta de Médico",
                    "medico": "Saúde/Falta de Médico",
                    "lixo": "Coleta de Lixo",
                    "coleta": "Coleta de Lixo",
                }

                suggested_normalized = suggested_category_name.lower().strip()
                if suggested_normalized in category_mapping:
                    suggested_category_name = category_mapping[suggested_normalized]

                suggested_category = ManifestationCategory.objects.filter(
                    name__iexact=suggested_category_name,
                    is_active=True,
                ).first()

                if not suggested_category:
                    suggested_category = ManifestationCategory.objects.filter(
                        name__icontains=suggested_category_name,
                        is_active=True,
                    ).first()

                if not suggested_category:
                    for category in ManifestationCategory.objects.filter(is_active=True):
                        category_name_lower = category.name.lower()
                        if any(keyword.lower() in category_name_lower for keyword in keywords):
                            suggested_category = category
                            break
                        if suggested_category_name.lower() in category_name_lower:
                            suggested_category = category
                            break

                if not suggested_category:
                    keywords_lower = [k.lower() for k in keywords] if keywords else []
                    description_lower = text.lower()

                    iluminacao_keywords = [
                        "poste",
                        "luz",
                        "lâmpada",
                        "lampada",
                        "iluminação",
                        "iluminacao",
                        "piscando",
                        "apagando",
                        "acendendo",
                        "apagada",
                        "queimada",
                        "luminária",
                    ]
                    if any(kw in keywords_lower for kw in iluminacao_keywords) or any(
                        kw in description_lower for kw in iluminacao_keywords
                    ):
                        suggested_category = ManifestationCategory.objects.filter(
                            name__icontains="Iluminação"
                        ).first()
                    elif any(
                        kw
                        in [
                            "buraco",
                            "rua",
                            "calçada",
                            "calcada",
                            "pavimentação",
                            "pavimentacao",
                            "asfalto",
                        ]
                        for kw in keywords_lower
                    ) or any(
                        kw
                        in description_lower
                        for kw in [
                            "buraco",
                            "rua",
                            "calçada",
                            "calcada",
                            "pavimentação",
                            "pavimentacao",
                        ]
                    ):
                        suggested_category = ManifestationCategory.objects.filter(
                            name__icontains="Pavimentação"
                        ).first()
                    elif any(
                        kw in ["lixo", "coleta", "lixeira", "lixeiro"] for kw in keywords_lower
                    ) or any(
                        kw in description_lower for kw in ["lixo", "coleta", "lixeira"]
                    ):
                        suggested_category = ManifestationCategory.objects.filter(
                            name__icontains="Lixo"
                        ).first()
                    elif any(
                        kw
                        in [
                            "saúde",
                            "saude",
                            "médico",
                            "medico",
                            "hospital",
                            "posto",
                            "unidade",
                        ]
                        for kw in keywords_lower
                    ) or any(
                        kw
                        in description_lower
                        for kw in ["saúde", "saude", "médico", "medico", "hospital"]
                    ):
                        suggested_category = ManifestationCategory.objects.filter(
                            name__icontains="Saúde"
                        ).first()

            usage_data: Dict[str, Any] = {}

            result = {
                "sentiment_score": sentiment_score,
                "urgency_level": urgency_level,
                "intent": intent,
                "suggested_category": suggested_category,
                "suggested_category_name": (
                    suggested_category.name if suggested_category else suggested_category_name
                ),
                "keywords": keywords,
                "summary": summary,
                "raw_ai_response": {
                    "model": response.json().get("model", model) if isinstance(response.json(), dict) else model,
                    "api_base": api_base,
                    "usage": usage_data,
                    "response_text": ai_response_text,
                    "parsed_json": ai_data,
                },
            }

            if save_to_db and manifestation_instance:
                nlp_analysis, created = NLPAnalysis.objects.update_or_create(
                    manifestation=manifestation_instance,
                    defaults={
                        "sentiment_score": sentiment_score,
                        "urgency_level": urgency_level,
                        "intent": intent,
                        "suggested_category": suggested_category,
                        "keywords": keywords,
                        "summary": summary,
                        "raw_ai_response": {
                            "model": model,
                            "api_base": api_base,
                            "usage": usage_data,
                            "response_text": ai_response_text,
                            "parsed_json": ai_data,
                            "full_response": {
                                "id": None,
                                "created": None,
                                "model": model,
                            },
                        },
                        "ai_model_used": model,
                        "analysis_version": getattr(
                            settings, "NLP_ANALYSIS_VERSION", "1.0"
                        ),
                    },
                )

                logger.info(
                    "Análise de IA concluída para manifestação %s. "
                    "Sentimento: %.2f, Urgência: %s, Categoria sugerida: %s",
                    manifestation_instance.protocol,
                    sentiment_score,
                    urgency_level,
                    suggested_category_name,
                )
                from intelligence.router import route_manifestation

                route_manifestation(manifestation_instance)
                return nlp_analysis

            logger.info(
                "Análise de IA concluída (rascunho). "
                "Sentimento: %.2f, Urgência: %s, Categoria sugerida: %s",
                sentiment_score,
                urgency_level,
                suggested_category_name,
            )

            return result

        except Exception as e:
            logger.error(
                "Erro ao analisar texto com LLM (Gabinete AI Kernel): %s",
                e,
                exc_info=True,
            )
            return None

    @staticmethod
    def analyze_manifestation(manifestation_instance):
        """
        Analisa uma manifestação usando LLM e salva o resultado no banco de dados.
        Wrapper para analyze_text com save_to_db=True.
        
        Args:
            manifestation_instance: Instância de Manifestation a ser analisada
            
        Returns:
            NLPAnalysis: Instância criada/atualizada ou None em caso de erro
        """
        return LLMService.analyze_text(
            text=manifestation_instance.description,
            save_to_db=True,
            manifestation_instance=manifestation_instance
        )


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """
    Distância em metros entre dois pontos (Haversine).
    """
    import math
    R = 6371000  # Raio da Terra em metros
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class DeduplicationService:
    """
    Serviço de detecção de duplicidade híbrida (geográfica + semântica).
    Identifica manifestações abertas que sejam simultaneamente:
    - Fisicamente próximas (box geográfico de ~100m)
    - Semanticamente idênticas (busca vetorial com threshold L2 / distância vetorial)
    
    Não agrupa automaticamente; apenas sugere e persiste em potential_duplicate.
    """
    # Threshold de similaridade calibrado para o modelo 'mxbai-embed-large' (1024d)
    # em textos curtos de ouvidoria, equivalente a ~74% de similaridade (Cosine Distance ~0.26).
    DUPLICITY_THRESHOLD = 0.26
    
    # Margem geográfica para pré-filtro (aproximadamente 100 metros)
    GEOGRAPHIC_MARGIN = 0.001  # graus (~111 metros)

    @staticmethod
    def detect_duplicates(manifestation):
        """
        Algoritmo híbrido de detecção de duplicidade:
        1. Pré-filtro geográfico (box de +/- 0.001 graus)
        2. Busca vetorial semântica (L2 distance)
        3. Threshold de 0.35 para considerar duplicata
        
        Returns:
            Manifestation ou None: manifestação sugerida como duplicata
        """
        from reports.models import Manifestation
        from pgvector.django import L2Distance

        # Validação: precisa ter localização e embedding
        if manifestation.latitude is None or manifestation.longitude is None:
            logger.debug(
                f"Manifestation {manifestation.protocol} sem localização. "
                "Impossível detectar duplicidade geográfica."
            )
            return None
        
        if manifestation.embedding is None:
            logger.debug(
                f"Manifestation {manifestation.protocol} sem embedding. "
                "Aguardando geração automática via signal."
            )
            return None
        
        # Verificar se embedding tem dados válidos
        try:
            import numpy as np
            if isinstance(manifestation.embedding, np.ndarray):
                has_embedding = manifestation.embedding.size > 0
            else:
                has_embedding = len(manifestation.embedding) > 0
        except (TypeError, AttributeError, ImportError):
            has_embedding = manifestation.embedding is not None
        
        if not has_embedding:
            logger.debug(
                f"Manifestation {manifestation.protocol} tem embedding vazio. "
                "Aguardando geração automática via signal."
            )
            return None

        # Status que indicam problemas ativos (não resolvidos/encerrados)
        # Buscar em QUALQUER status que não seja CLOSED/RESOLVED
        # Isso permite anexar novas manifestações a chamados já em andamento
        active_statuses = [
            Manifestation.STATUS_WAITING_TRIAGE,
            Manifestation.STATUS_IN_ANALYSIS,
            Manifestation.STATUS_FORWARDED,
            Manifestation.STATUS_DUPLICATE_FORWARDED,  # Incluir duplicatas já processadas
        ]

        # Pré-filtro geográfico: Box de +/- 0.001 graus (~100 metros)
        lat_margin = DeduplicationService.GEOGRAPHIC_MARGIN
        lon_margin = DeduplicationService.GEOGRAPHIC_MARGIN
        
        target_lat = float(manifestation.latitude)
        target_lon = float(manifestation.longitude)

        # Buscar candidatos no box geográfico com status ativo e com embedding
        candidates = (
            Manifestation.objects
            .filter(
                # Box geográfico aproximado
                latitude__range=(target_lat - lat_margin, target_lat + lat_margin),
                longitude__range=(target_lon - lon_margin, target_lon + lon_margin),
                # Status ativo
                status__in=active_statuses,
                # Com embedding gerado
                embedding__isnull=False,
            )
            .exclude(id=manifestation.id)
        )

        if not candidates.exists():
            logger.debug(
                f"Nenhum candidato encontrado no box geográfico para {manifestation.protocol}"
            )
            return None

        # Busca vetorial semântica: calcular distância L2 para cada candidato
        try:
            # Anotar distância L2 e ordenar por menor distância
            candidates_with_distance = (
                candidates
                .annotate(distance=L2Distance('embedding', manifestation.embedding))
                .order_by('distance')
            )
            
            # Pegar o candidato mais próximo
            closest = candidates_with_distance.first()
            
            if not closest:
                return None
            
            distance_value = float(closest.distance)
            
            logger.info(
                f"Manifestation {manifestation.protocol}: candidato mais próximo é "
                f"{closest.protocol} com distância L2 = {distance_value:.4f}"
            )
            
            # Decisão: threshold de 0.35
            if distance_value < DeduplicationService.DUPLICITY_THRESHOLD:
                # Encontrou duplicata!
                # Se a manifestação "Pai" já está em andamento (FORWARDED ou IN_ANALYSIS),
                # marcar a nova como DUPLICATE_FORWARDED e agrupar automaticamente
                from reports.models import Manifestation
                
                # Verificar se a manifestação encontrada é "Pai" (is_primary=True)
                # ou se é uma manifestação única que pode virar pai
                is_parent_active = (
                    closest.is_primary or 
                    closest.status in [Manifestation.STATUS_FORWARDED, Manifestation.STATUS_IN_ANALYSIS]
                )
                
                if is_parent_active:
                    # Cenário: Pai já está em andamento
                    # 1. Vincular a nova manifestação ao grupo
                    if closest.is_primary:
                        parent = closest
                    else:
                        # Se não é pai ainda, tornar ela pai
                        closest.is_primary = True
                        closest.save(update_fields=['is_primary'])
                        parent = closest
                    
                    # 2. Marcar a nova como filha e auto-arquivar
                    manifestation.related_group = parent
                    manifestation.is_primary = False
                    manifestation.status = Manifestation.STATUS_DUPLICATE_FORWARDED
                    manifestation.potential_duplicate = closest
                    manifestation.save(update_fields=['related_group', 'is_primary', 'status', 'potential_duplicate'])
                    
                    logger.info(
                        f"✅ Duplicata anexada automaticamente: {manifestation.protocol} foi agrupada "
                        f"à manifestação {parent.protocol} (já em andamento). "
                        f"Status alterado para DUPLICATE_FORWARDED."
                    )
                else:
                    # Cenário: Pai ainda está em triagem
                    # Apenas sugerir (comportamento original)
                    manifestation.potential_duplicate = closest
                    manifestation.save(update_fields=['potential_duplicate'])
                    
                    logger.info(
                        f"✅ Duplicidade detectada: {manifestation.protocol} é similar a "
                        f"{closest.protocol} (distância L2: {distance_value:.4f} < threshold: "
                        f"{DeduplicationService.DUPLICITY_THRESHOLD})"
                    )
                
                return closest
            else:
                logger.debug(
                    f"Manifestation {manifestation.protocol}: candidato mais próximo "
                    f"({closest.protocol}) está acima do threshold "
                    f"(distância: {distance_value:.4f} >= {DeduplicationService.DUPLICITY_THRESHOLD}). "
                    "Não é duplicata."
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Erro ao calcular distância vetorial para {manifestation.protocol}: {str(e)}",
                exc_info=True
            )
            return None
