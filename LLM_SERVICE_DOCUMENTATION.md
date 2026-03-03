# 🤖 Serviço LLM Flexível - ProjectOuvidoria

## Visão Geral

O serviço de análise NLP foi refatorado para ser **flexível e compatível** com múltiplos provedores de LLM que seguem a API compatível com OpenAI:

- ✅ **OpenAI** (GPT-4, GPT-3.5, etc.)
- ✅ **Groq** (Llama 3, Mixtral, etc.)
- ✅ **LocalLLM** (LM Studio, Ollama, etc.)

## Configuração

### Variáveis de Ambiente (.env)

```env
# LLM Configuration
OPENAI_API_KEY=sua-chave-aqui
OPENAI_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
NLP_ANALYSIS_VERSION=1.0
```

### Exemplos de Configuração

#### OpenAI (Padrão)
```env
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

#### Groq (Llama 3)
```env
OPENAI_API_KEY=gsk_...
OPENAI_API_BASE=https://api.groq.com/openai/v1
LLM_MODEL=llama3-70b-8192
```

#### LocalLLM (LM Studio / Ollama)
```env
OPENAI_API_KEY=lm-studio  # Pode ser qualquer string
OPENAI_API_BASE=http://localhost:1234/v1
LLM_MODEL=llama3-8b-instruct
```

## Arquitetura

### `LLMService` (intelligence/services.py)

**Classe Principal**: `LLMService`

**Método**: `analyze_manifestation(manifestation_instance)`

**Características**:
- ✅ Suporta qualquer API compatível com OpenAI
- ✅ Configurável via `OPENAI_API_BASE`
- ✅ Extração inteligente de JSON (para modelos verbosos)
- ✅ Fallback automático se `response_format` não for suportado
- ✅ Tratamento robusto de erros

### Extração de JSON

O método `extract_json_from_text()` trata modelos verbosos que podem retornar:

1. **JSON puro**: `{"sentiment_score": 0.5, ...}`
2. **JSON em markdown**: ````json\n{...}\n````
3. **JSON com texto adicional**: `Aqui está o JSON: {...}`

**Estratégias de extração**:
1. Tentativa de parse direto
2. Extração de code blocks markdown
3. Busca por primeiro objeto JSON válido
4. Busca por padrão de chaves balanceadas

## Prompt Otimizado

### System Message
```
Você é um Analista de Ouvidoria da Prefeitura. 
Sua tarefa é categorizar manifestações de cidadãos.

Retorne APENAS um objeto JSON válido. 
Não inclua markdown ```json``` ou texto adicional.

O JSON deve conter exatamente estes campos:
- sentiment_score: float entre -1.0 e 1.0
- urgency_level: int de 1 a 5
- suggested_category: string curta
- summary: string com resumo executivo
- keywords: array de strings com 3 a 5 palavras-chave
```

### User Message
Envia diretamente: `manifestation.description`

## Fluxo de Execução

```
Manifestation Criada
    ↓
Signal (post_save)
    ↓
Thread Assíncrona
    ↓
LLMService.analyze_manifestation()
    ↓
Cliente OpenAI (base_url configurável)
    ↓
API do Provedor (OpenAI/Groq/LocalLLM)
    ↓
Extração de JSON (com fallbacks)
    ↓
NLPAnalysis Criado/Atualizado
```

## Tratamento de Compatibilidade

### response_format

Alguns modelos locais podem não suportar `response_format={"type": "json_object"}`.

**Solução**: Try/except que tenta com `response_format` primeiro, e se falhar, tenta sem ele.

```python
try:
    call_params['response_format'] = {"type": "json_object"}
    response = client.chat.completions.create(**call_params)
except Exception:
    # Fallback: tentar sem response_format
    call_params.pop('response_format', None)
    response = client.chat.completions.create(**call_params)
```

### Uso de Tokens

O sistema verifica se `response.usage` está disponível antes de acessar:
- Alguns provedores podem não retornar informações de uso
- O código trata isso graciosamente

## Modelos Testados

### ✅ Groq - Llama 3 70B
- **Base URL**: `https://api.groq.com/openai/v1`
- **Modelo**: `llama3-70b-8192`
- **Status**: Funcional ✅
- **Observação**: Pode ser verboso, mas a extração de JSON funciona

### ✅ OpenAI - GPT-4o-mini
- **Base URL**: `https://api.openai.com/v1`
- **Modelo**: `gpt-4o-mini`
- **Status**: Funcional ✅
- **Observação**: Suporta `response_format` nativamente

### ⚠️ LocalLLM (LM Studio / Ollama)
- **Base URL**: `http://localhost:1234/v1` (ou porta configurada)
- **Modelo**: Depende do modelo carregado
- **Status**: Compatível (requer teste)
- **Observação**: Pode não suportar `response_format`

## Logs

O sistema registra informações úteis para debug:

```
INFO: Iniciando análise de IA para manifestação OUV-20240216-A3B4C (Modelo: llama3-70b-8192, Base: https://api.groq.com/openai/v1)
INFO: Análise de IA concluída para manifestação OUV-20240216-A3B4C. Sentimento: -0.75, Urgência: 4, Categoria sugerida: Infraestrutura
```

## Validações

### Sentiment Score
- Range: -1.0 a 1.0
- Clamp automático se fora do range

### Urgency Level
- Range: 1 a 5
- Clamp automático se fora do range

### Keywords
- Garantido como lista (converte se necessário)
- 3 a 5 palavras-chave esperadas

### Suggested Category
- Busca inteligente no banco de dados
- Busca por nome (case-insensitive)
- Busca por palavras-chave se não encontrar
- Pode ser `None` se não encontrar correspondência

## Persistência

### NLPAnalysis

Todos os dados são salvos em `NLPAnalysis`:

- `sentiment_score`: Float extraído
- `urgency_level`: Int extraído
- `suggested_category`: ForeignKey (pode ser None)
- `keywords`: JSONField (lista de strings)
- `summary`: TextField
- `raw_ai_response`: JSONField completo com:
  - `model`: Modelo usado
  - `api_base`: Base URL usada
  - `usage`: Tokens consumidos (se disponível)
  - `response_text`: Resposta bruta
  - `parsed_json`: JSON parseado
  - `full_response`: Metadados completos

## Testes

### Teste com Groq

1. Configure `.env`:
```env
OPENAI_API_KEY=gsk_...
OPENAI_API_BASE=https://api.groq.com/openai/v1
LLM_MODEL=llama3-70b-8192
```

2. Crie uma manifestação:
```bash
curl -X POST http://localhost:8000/api/v1/reports/manifestations/ \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Buraco enorme na rua principal causando acidentes. Muito perigoso!",
    "origin": "web"
  }'
```

3. Aguarde alguns segundos e verifique:
```bash
curl http://localhost:8000/api/v1/reports/manifestations/{id}/
```

4. Verifique o campo `nlp_analysis` no response

## Troubleshooting

### Erro: "OPENAI_API_KEY não configurada"
- **Solução**: Configure `OPENAI_API_KEY` no `.env`

### Erro: "Connection refused"
- **Solução**: Verifique se `OPENAI_API_BASE` está correto
- Para LocalLLM: Verifique se o servidor está rodando

### Erro: "JSON não encontrado na resposta"
- **Solução**: O modelo pode ser muito verboso
- O sistema tenta extrair JSON automaticamente
- Verifique os logs para ver a resposta bruta

### Categoria sugerida não encontrada
- **Comportamento esperado**: Se não encontrar correspondência, `suggested_category` será `None`
- **Solução**: Crie categorias no banco ou ajuste os nomes sugeridos

## Melhorias Futuras

1. **Cache de Análises**: Cachear análises similares
2. **Retry Logic**: Retry automático em caso de falha
3. **Métricas**: Dashboard com estatísticas por provedor
4. **A/B Testing**: Comparar resultados entre modelos
5. **Rate Limiting**: Controle de taxa por provedor
6. **Fallback Chain**: Tentar múltiplos provedores em sequência

## Status: ✅ IMPLEMENTADO

O serviço está funcional e pronto para uso com Groq, OpenAI ou LocalLLM!
