import json
import re
import logging
import os
from django.conf import settings
from openai import OpenAI
from .models import NLPAnalysis
from reports.models import ManifestationCategory
from core.services.geocoding_service import GeocodingService

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

            # Carregar categorias válidas diretamente do banco para guiar o LLM
            categorias_validas = list(
                ManifestationCategory.objects.filter(is_active=True).values_list('name', flat=True)
            )
            categorias_str = (
                ", ".join(categorias_validas)
                if categorias_validas
                else "Infraestrutura, Iluminação, Saúde, Trânsito, Outros"
            )
            
            # Preparar o prompt do sistema (inclui múltiplas demandas e triagem de castração)
            system_message = f"""
Você é um Analista Sênior de Ouvidoria e Serviços Públicos. Sua tarefa é categorizar manifestações de cidadãos.

Responda APENAS com um JSON válido, contendo EXATAMENTE as seguintes chaves:
- 'intent': Use "COMPLAINT", "SUGGESTION", "INFORMATION", "DENUNCIATION", ou "SERVICE_CASTRATION" (para castração de cães/gatos).
- 'macro_category': APENAS um destes valores: [{categorias_str}].
- 'category_detail': O serviço específico (ex: "Castração", "Tapa-buraco").
- 'urgency_level': Inteiro de 1 a 5.
- 'sentiment': Float de -1.0 a 1.0.
- 'summary': Resumo de 5 a 10 palavras.
- 'keywords': Lista de 3 a 5 palavras.
- 'has_multiple_demands': booleano (true se o cidadão relatar mais de um problema físico ou serviço distinto no mesmo texto).
- 'all_demands': Lista de objetos com os problemas encontrados. Cada objeto deve ter: {{"macro_category": "...", "category_detail": "...", "specific_text": "trecho exato do cidadão"}}. Se houver apenas um problema, retorne a lista com 1 objeto.
- 'service_data': Se a intent for "SERVICE_CASTRATION", retorne:
    {{
      "animal_type": "cão" ou "gato",
      "animal_gender": "macho" ou "fêmea",
      "animal_age": "idade extraída",
      "animal_weight": "peso extraído",
      "medical_condition": "condição mencionada",
      "eligibility_error": "MENSAGEM DE ERRO (se reprovar) ou null (se aprovado/incompleto)"
    }}
  Se não for castração, retorne null.

REGRAS DE CASTRAÇÃO (Preencha 'eligibility_error' se reprovar):
1. Cães/Gatos machos a partir de 6 meses. Fêmeas a partir de 4 meses. Máximo: 10 anos.
2. Peso mínimo: 2 kg.
3. Fêmeas não podem estar prenhas, amamentando ou no cio.
4. Sem doenças graves (cardiopatia, etc).
Ex: "Infelizmente, animais acima de 10 anos não são contemplados."
"""
            
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
            
            # Extrair os dados estruturados (formato flat + service_data para castração)
            sentiment_score = float(ai_data.get('sentiment', ai_data.get('sentiment_score', 0.0)))
            intent = ai_data.get('intent', 'COMPLAINT')
            global_summary = ai_data.get('summary', ai_data.get('global_summary', ''))
            global_keywords = ai_data.get('keywords', ai_data.get('global_keywords', []))
            service_data = ai_data.get('service_data', None)

            # Castração: "eligibility_error" só deve existir se REPROVAR.
            # Alguns modelos retornam frases de "dados insuficientes" como erro; tratamos como incompleto (null).
            if intent == "SERVICE_CASTRATION" and isinstance(service_data, dict):
                eligibility_error = service_data.get("eligibility_error")
                if isinstance(eligibility_error, str) and re.search(r"insuficient", eligibility_error, re.IGNORECASE):
                    service_data["eligibility_error"] = None

            # Formato novo: campos no nível raiz; fallback para demands (compatibilidade)
            demands = ai_data.get('demands', [])
            if demands:
                primary_demand = demands[0]
                urgency_level = int(primary_demand.get('urgency_level', 3))
                macro_category = primary_demand.get('macro_category', '')
                category_detail = primary_demand.get('category_detail', '')
                has_multiple_demands = len(demands) > 1
            else:
                urgency_level = int(ai_data.get('urgency_level', 3))
                macro_category = ai_data.get('macro_category', '')
                category_detail = ai_data.get('category_detail', '')
                has_multiple_demands = False
                demands = [{
                    "macro_category": macro_category or "Outros",
                    "category_detail": category_detail or "Não classificado",
                    "urgency_level": urgency_level,
                    "specific_text": text,
                }]

            # Permitir que o modelo retorne explicitamente múltiplas demandas no novo formato
            has_multiple_demands = ai_data.get('has_multiple_demands', has_multiple_demands)
            all_demands = ai_data.get('all_demands', demands)

            # Garantir que castração apareça como demanda explícita quando a intent for SERVICE_CASTRATION,
            # mesmo que o modelo não a liste em all_demands.
            if intent == "SERVICE_CASTRATION":
                castration_present = False
                for d in all_demands:
                    try:
                        detail = str((d or {}).get("category_detail", "")).lower()
                        macro = str((d or {}).get("macro_category", "")).lower()
                    except Exception:
                        detail = ""
                        macro = ""
                    if "castra" in detail or "castra" in macro:
                        castration_present = True
                        break

                if not castration_present:
                    # Adiciona uma demanda sintética de castração sem depender do modelo
                    all_demands.append({
                        "macro_category": macro_category or "Saúde Animal",
                        "category_detail": category_detail or "Castração",
                        "urgency_level": urgency_level,
                        "specific_text": text,
                    })

            # Validar intent (inclui SERVICE_CASTRATION para triagem ativa)
            valid_intents = ["COMPLAINT", "SUGGESTION", "INFORMATION", "DENUNCIATION", "SERVICE_CASTRATION"]
            if intent not in valid_intents:
                intent = 'COMPLAINT'  # Default seguro

            # Garantir que global_keywords é uma lista
            if not isinstance(global_keywords, list):
                global_keywords = []

            # Validar ranges
            sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp entre -1 e 1
            urgency_level = max(1, min(5, urgency_level))  # Clamp entre 1 e 5

            # Buscar categoria sugerida no banco pela macro_category da demanda primária
            suggested_category = None
            suggested_category_name = macro_category.strip() if macro_category else ''
            if suggested_category_name:
                suggested_category = ManifestationCategory.objects.filter(
                    name__iexact=suggested_category_name,
                    is_active=True
                ).first()
            
            # Preparar dados de uso (pode não estar disponível em todos os provedores)
            usage_data = {}
            if hasattr(response, 'usage') and response.usage:
                usage_data = {
                    'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                    'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                    'total_tokens': getattr(response.usage, 'total_tokens', 0),
                }
            
            # Preparar resultado (demanda primária + service_data para castração)
            result = {
                'sentiment_score': sentiment_score,
                'urgency_level': urgency_level,
                'intent': intent,
                'suggested_category': suggested_category,
                'suggested_category_name': suggested_category.name if suggested_category else macro_category,
                'category': suggested_category_name,
                'category_detail': category_detail,
                'keywords': global_keywords,
                'summary': global_summary,
                'has_multiple_demands': has_multiple_demands,
                'all_demands': all_demands,
                'service_data': service_data,
                'raw_ai_response': {
                    'model': response.model,
                    'api_base': api_base,
                    'usage': usage_data,
                    'response_text': ai_response_text,
                    'parsed_json': ai_data,
                },
            }
            
            # Se deve salvar no banco (campos do NLPAnalysis usam demanda primária; lista completa em parsed_json)
            if save_to_db and manifestation_instance:
                nlp_analysis, created = NLPAnalysis.objects.update_or_create(
                    manifestation=manifestation_instance,
                    defaults={
                        'sentiment_score': sentiment_score,
                        'urgency_level': urgency_level,
                        'intent': intent,
                        'suggested_category': suggested_category,
                        'keywords': global_keywords,
                        'summary': global_summary,
                        'raw_ai_response': {
                            'model': response.model,
                            'api_base': api_base,
                            'usage': usage_data,
                            'response_text': ai_response_text,
                            'parsed_json': ai_data,  # contém demands e has_multiple_demands para uso futuro
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

                # Se o modelo retornou um detalhe de categoria e o campo existir na Manifestation,
                # preenche manifestation.category_detail para uso posterior nos painéis.
                if category_detail and hasattr(manifestation_instance, "category_detail"):
                    manifestation_instance.category_detail = category_detail
                    manifestation_instance.save(update_fields=["category_detail"])

                # Persistir service_data (ex: dados da castração) quando o campo existir
                if service_data and hasattr(manifestation_instance, "service_data"):
                    manifestation_instance.service_data = service_data
                    manifestation_instance.save(update_fields=["service_data"])

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

        Antes da análise de IA, tenta obter coordenadas geográficas a partir do endereço,
        caso a manifestação tenha endereço mas ainda não tenha latitude/longitude.
        
        Args:
            manifestation_instance: Instância de Manifestation a ser analisada
            
        Returns:
            NLPAnalysis: Instância criada/atualizada ou None em caso de erro
        """
        # Tenta buscar coordenadas se houver endereço, mas não houver lat/lon
        if manifestation_instance.location_address and (
            not manifestation_instance.latitude or not manifestation_instance.longitude
        ):
            lat, lon = GeocodingService.get_coordinates(manifestation_instance.location_address)
            if lat and lon:
                manifestation_instance.latitude = lat
                manifestation_instance.longitude = lon
                manifestation_instance.save(update_fields=["latitude", "longitude"])

        return LLMService.analyze_text(
            text=manifestation_instance.description,
            save_to_db=True,
            manifestation_instance=manifestation_instance,
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
