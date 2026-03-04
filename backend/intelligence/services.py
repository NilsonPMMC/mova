import json
import re
import logging
import os
from django.conf import settings
from openai import OpenAI
from .models import NLPAnalysis
from reports.models import ManifestationCategory

logger = logging.getLogger(__name__)


class LLMService:
    """
    Serviço flexível para análise de manifestações usando LLMs compatíveis com OpenAI API
    Suporta: OpenAI, Groq, LocalLLM (via OpenAI-compatible API)
    """
    
    @staticmethod
    def extract_json_from_text(text):
        """
        Extrai JSON de um texto que pode conter markdown ou texto adicional.
        Útil para modelos verbosos como Llama 3.
        
        Args:
            text: Texto que pode conter JSON
            
        Returns:
            dict: JSON extraído ou None se não encontrar
        """
        # Tentar parsear diretamente primeiro
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Tentar extrair JSON de markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Tentar encontrar primeiro objeto JSON válido
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Tentar encontrar qualquer JSON válido no texto
        start_idx = text.find('{')
        if start_idx != -1:
            # Encontrar o último } correspondente
            brace_count = 0
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            return json.loads(text[start_idx:i+1])
                        except json.JSONDecodeError:
                            break
        
        return None
    
    @staticmethod
    def analyze_text(text, save_to_db=False, manifestation_instance=None):
        """
        Analisa um texto usando LLM e retorna os dados estruturados.
        
        Args:
            text: Texto a ser analisado
            save_to_db: Se True, salva no banco (requer manifestation_instance)
            manifestation_instance: Instância de Manifestation (obrigatório se save_to_db=True)
        
        Returns:
            dict: Dados estruturados da análise ou None em caso de erro
        """
        if save_to_db and not manifestation_instance:
            raise ValueError("manifestation_instance é obrigatório quando save_to_db=True")
        
        try:
            # Configurações da API
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            api_base = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1')
            model = getattr(settings, 'LLM_MODEL', 'gpt-4o-mini')
            
            if not api_key:
                logger.warning("OPENAI_API_KEY não configurada. Análise não será executada.")
                return None
            
            # Remover variáveis de ambiente de proxy que podem causar conflito com httpx
            import httpx
            env_backup = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    env_backup[var] = os.environ.pop(var)

            try:
                # Criar cliente httpx sem proxies (variáveis de ambiente já foram removidas)
                http_client = httpx.Client(timeout=30.0)

                # Criar cliente OpenAI com cliente HTTP customizado
                if api_base != 'https://api.openai.com/v1':
                    client = OpenAI(
                        api_key=api_key,
                        base_url=api_base,
                        http_client=http_client
                    )
                else:
                    client = OpenAI(
                        api_key=api_key,
                        http_client=http_client
                    )
            finally:
                # Restaurar variáveis de ambiente de proxy
                for var, value in env_backup.items():
                    os.environ[var] = value
            
            # Preparar o prompt do sistema
            system_message = """Você é um Analista de Ouvidoria da Prefeitura. Sua tarefa é categorizar manifestações de cidadãos.

Retorne APENAS um objeto JSON válido. Não inclua markdown ```json``` ou texto adicional.

O JSON deve conter exatamente estes campos:
- sentiment_score: float entre -1.0 (muito negativo/raiva) e 1.0 (positivo/elogio)
- urgency_level: int de 1 (pouco urgente) a 5 (crítico/risco de vida)
- intent: string com uma destas opções EXATAS:
  * "COMPLAINT" (Reclamação - problema que precisa ser resolvido)
  * "SUGGESTION" (Sugestão - ideia ou melhoria proposta)
  * "INFORMATION" (Dúvida/Informação - pergunta ou busca de informação)
  * "DENUNCIATION" (Denúncia - irregularidade grave)
- suggested_category: string curta com o nome EXATO de uma destas categorias:
  * "Iluminação Pública" (para problemas com postes, lâmpadas, luzes piscando/apagadas)
  * "Buraco em Via/Pavimentação" (para buracos, calçadas, pavimentação)
  * "Saúde/Falta de Médico" (para problemas em unidades de saúde, falta de médicos)
  * "Coleta de Lixo" (para problemas com coleta, lixeiras)
  * "Zeladoria" (para limpeza, capina, poda)
  * "Trânsito" (para sinalização, semáforos, faixas)
  * "Segurança" (para problemas de segurança pública)
  * "Meio Ambiente" (para questões ambientais)
- summary: string com resumo executivo de uma frase
- keywords: array de strings com 3 a 5 palavras-chave principais extraídas do texto

IMPORTANTE: 
- Retorne APENAS o JSON válido, sem explicações, sem markdown.
- Use o nome EXATO da categoria da lista acima.
- Para problemas com "poste", "luz", "lâmpada", "iluminação", "piscando", "apagando", "acendendo" → use "Iluminação Pública".
- Para problemas com "buraco", "rua", "calçada", "pavimentação" → use "Buraco em Via/Pavimentação".
- Para dúvidas, perguntas como "onde", "como", "quando", "qual" → use "INFORMATION".
- Para reclamações sobre problemas → use "COMPLAINT".
- Para sugestões de melhoria → use "SUGGESTION".
- Para denúncias de irregularidades graves → use "DENUNCIATION"."""
            
            # Preparar o prompt do usuário com o relato
            user_message = text
            
            # Chamar a API do LLM
            logger.info(
                f"Iniciando análise de IA para texto "
                f"(Modelo: {model}, Base: {api_base})"
            )
            
            # Preparar parâmetros da chamada
            call_params = {
                'model': model,
                'messages': [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                'temperature': 0.3,  # Baixa temperatura para respostas mais consistentes
            }
            
            # Tentar usar response_format se suportado (OpenAI, Groq suportam)
            # Alguns modelos locais podem não suportar, então fazemos try/except
            try:
                call_params['response_format'] = {"type": "json_object"}
                response = client.chat.completions.create(**call_params)
            except Exception as e:
                # Se não suportar response_format, tentar sem ele
                logger.debug(f"response_format não suportado, tentando sem ele: {e}")
                call_params.pop('response_format', None)
                response = client.chat.completions.create(**call_params)
            
            # Extrair a resposta
            ai_response_text = response.choices[0].message.content
            
            # Parsear o JSON retornado (com tratamento para modelos verbosos)
            ai_data = LLMService.extract_json_from_text(ai_response_text)
            
            if not ai_data:
                logger.error(
                    f"Erro ao extrair JSON da resposta do LLM. "
                    f"Resposta recebida: {ai_response_text[:500]}"
                )
                return None
            
            # Extrair os dados estruturados
            sentiment_score = float(ai_data.get('sentiment_score', 0.0))
            urgency_level = int(ai_data.get('urgency_level', 3))
            intent = ai_data.get('intent', 'COMPLAINT')
            suggested_category_name = ai_data.get('suggested_category', '')
            summary = ai_data.get('summary', '')
            keywords = ai_data.get('keywords', [])
            
            # Validar intent
            valid_intents = ['COMPLAINT', 'SUGGESTION', 'INFORMATION', 'DENUNCIATION']
            if intent not in valid_intents:
                intent = 'COMPLAINT'  # Default seguro
            
            # Garantir que keywords é uma lista
            if not isinstance(keywords, list):
                keywords = []
            
            # Validar ranges
            sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp entre -1 e 1
            urgency_level = max(1, min(5, urgency_level))  # Clamp entre 1 e 5
            
            # Tentar encontrar categoria sugerida no banco
            suggested_category = None
            if suggested_category_name:
                # Limpar o nome da categoria (remover espaços extras, etc)
                suggested_category_name = suggested_category_name.strip()
                
                # Mapeamento de sinônimos para categorias
                category_mapping = {
                    'iluminação pública': 'Iluminação Pública',
                    'iluminacao publica': 'Iluminação Pública',
                    'luz': 'Iluminação Pública',
                    'poste': 'Iluminação Pública',
                    'lâmpada': 'Iluminação Pública',
                    'lampada': 'Iluminação Pública',
                    'buraco': 'Buraco em Via/Pavimentação',
                    'pavimentação': 'Buraco em Via/Pavimentação',
                    'pavimentacao': 'Buraco em Via/Pavimentação',
                    'rua': 'Buraco em Via/Pavimentação',
                    'calçada': 'Buraco em Via/Pavimentação',
                    'calcada': 'Buraco em Via/Pavimentação',
                    'saúde': 'Saúde/Falta de Médico',
                    'saude': 'Saúde/Falta de Médico',
                    'médico': 'Saúde/Falta de Médico',
                    'medico': 'Saúde/Falta de Médico',
                    'lixo': 'Coleta de Lixo',
                    'coleta': 'Coleta de Lixo',
                }
                
                # Normalizar nome sugerido
                suggested_normalized = suggested_category_name.lower().strip()
                
                # Verificar mapeamento
                if suggested_normalized in category_mapping:
                    suggested_category_name = category_mapping[suggested_normalized]
                
                # Buscar categoria por nome exato primeiro (case-insensitive)
                suggested_category = ManifestationCategory.objects.filter(
                    name__iexact=suggested_category_name,
                    is_active=True
                ).first()
                
                # Se não encontrar, buscar por nome parcial
                if not suggested_category:
                    suggested_category = ManifestationCategory.objects.filter(
                        name__icontains=suggested_category_name,
                        is_active=True
                    ).first()
                
                # Se ainda não encontrar, tentar buscar por palavras-chave
                if not suggested_category:
                    for category in ManifestationCategory.objects.filter(is_active=True):
                        category_name_lower = category.name.lower()
                        # Verificar se alguma palavra-chave está no nome da categoria
                        if any(keyword.lower() in category_name_lower for keyword in keywords):
                            suggested_category = category
                            break
                        # Verificar se o nome sugerido está no nome da categoria
                        if suggested_category_name.lower() in category_name_lower:
                            suggested_category = category
                            break
                
                # Busca inteligente por palavras-chave específicas na descrição também
                if not suggested_category:
                    keywords_lower = [k.lower() for k in keywords] if keywords else []
                    description_lower = text.lower()
                    
                    # Verificar palavras-chave relacionadas a iluminação
                    iluminacao_keywords = ['poste', 'luz', 'lâmpada', 'lampada', 'iluminação', 'iluminacao', 'piscando', 'apagando', 'acendendo', 'apagada', 'queimada', 'luminária']
                    if any(kw in keywords_lower for kw in iluminacao_keywords) or \
                       any(kw in description_lower for kw in iluminacao_keywords):
                        suggested_category = ManifestationCategory.objects.filter(name__icontains='Iluminação').first()
                    # Verificar palavras-chave relacionadas a buraco/pavimentação
                    elif any(kw in ['buraco', 'rua', 'calçada', 'calcada', 'pavimentação', 'pavimentacao', 'asfalto'] for kw in keywords_lower) or \
                         any(kw in description_lower for kw in ['buraco', 'rua', 'calçada', 'calcada', 'pavimentação', 'pavimentacao']):
                        suggested_category = ManifestationCategory.objects.filter(name__icontains='Pavimentação').first()
                    # Verificar palavras-chave relacionadas a lixo
                    elif any(kw in ['lixo', 'coleta', 'lixeira', 'lixeiro'] for kw in keywords_lower) or \
                         any(kw in description_lower for kw in ['lixo', 'coleta', 'lixeira']):
                        suggested_category = ManifestationCategory.objects.filter(name__icontains='Lixo').first()
                    # Verificar palavras-chave relacionadas a saúde
                    elif any(kw in ['saúde', 'saude', 'médico', 'medico', 'hospital', 'posto', 'unidade'] for kw in keywords_lower) or \
                         any(kw in description_lower for kw in ['saúde', 'saude', 'médico', 'medico', 'hospital']):
                        suggested_category = ManifestationCategory.objects.filter(name__icontains='Saúde').first()
            
            # Preparar dados de uso (pode não estar disponível em todos os provedores)
            usage_data = {}
            if hasattr(response, 'usage') and response.usage:
                usage_data = {
                    'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                    'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                    'total_tokens': getattr(response.usage, 'total_tokens', 0),
                }
            
            # Preparar resultado
            result = {
                'sentiment_score': sentiment_score,
                'urgency_level': urgency_level,
                'intent': intent,
                'suggested_category': suggested_category,
                'suggested_category_name': suggested_category.name if suggested_category else suggested_category_name,
                'keywords': keywords,
                'summary': summary,
                'raw_ai_response': {
                    'model': response.model,
                    'api_base': api_base,
                    'usage': usage_data,
                    'response_text': ai_response_text,
                    'parsed_json': ai_data,
                }
            }
            
            # Se deve salvar no banco
            if save_to_db and manifestation_instance:
                nlp_analysis, created = NLPAnalysis.objects.update_or_create(
                    manifestation=manifestation_instance,
                    defaults={
                        'sentiment_score': sentiment_score,
                        'urgency_level': urgency_level,
                        'intent': intent,
                        'suggested_category': suggested_category,
                        'keywords': keywords,
                        'summary': summary,
                        'raw_ai_response': {
                            'model': response.model,
                            'api_base': api_base,
                            'usage': usage_data,
                            'response_text': ai_response_text,
                            'parsed_json': ai_data,
                            'full_response': {
                                'id': getattr(response, 'id', None),
                                'created': getattr(response, 'created', None),
                                'model': response.model,
                            }
                        },
                        'ai_model_used': response.model,
                        'analysis_version': getattr(settings, 'NLP_ANALYSIS_VERSION', '1.0'),
                    }
                )
                
                logger.info(
                    f"Análise de IA concluída para manifestação {manifestation_instance.protocol}. "
                    f"Sentimento: {sentiment_score:.2f}, Urgência: {urgency_level}, "
                    f"Intenção: {intent}, Categoria sugerida: {suggested_category_name}"
                )
                from intelligence.router import route_manifestation
                route_manifestation(manifestation_instance)
                return nlp_analysis
            else:
                logger.info(
                    f"Análise de IA concluída (rascunho). "
                    f"Sentimento: {sentiment_score:.2f}, Urgência: {urgency_level}, "
                    f"Intenção: {intent}, Categoria sugerida: {suggested_category_name}"
                )
                
                return result
            
        except Exception as e:
            # Log do erro sem quebrar o sistema
            logger.error(
                f"Erro ao analisar texto com LLM: {str(e)}",
                exc_info=True
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
