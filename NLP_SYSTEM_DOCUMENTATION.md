# 🤖 Sistema de Análise NLP com OpenAI - ProjectOuvidoria

## Visão Geral

O sistema de análise NLP (Natural Language Processing) processa automaticamente todas as manifestações criadas pelos cidadãos, extraindo informações estruturadas usando a API da OpenAI GPT.

## Arquitetura

```
Manifestation Criada
    ↓
Signal (post_save)
    ↓
Thread Assíncrona (não trava o request)
    ↓
OpenAIService.analyze_manifestation()
    ↓
API OpenAI GPT
    ↓
NLPAnalysis Criado/Atualizado
```

## Componentes

### 1. `intelligence/services.py` - OpenAIService

**Classe**: `OpenAIService`

**Método Principal**: `analyze_manifestation(manifestation_instance)`

**Funcionalidades**:
- Conecta com a API da OpenAI usando a chave configurada
- Envia o relato do cidadão para análise
- Extrai informações estruturadas:
  - `sentiment_score`: Float entre -1.0 (muito negativo) e 1.0 (positivo)
  - `urgency_level`: Int de 1 (baixa) a 5 (crítica)
  - `suggested_category`: String com categoria sugerida
  - `summary`: Resumo técnico de uma frase
  - `keywords`: Lista de 3-5 palavras-chave
- Salva o resultado em `NLPAnalysis`
- Armazena resposta bruta da API para auditoria

**Tratamento de Erros**:
- Se API key não configurada: loga warning e retorna None
- Se API falhar: loga erro mas não quebra o sistema
- Validações de ranges (sentiment_score entre -1 e 1, urgency_level entre 1 e 5)

### 2. `intelligence/signals.py` - Gatilho Automático

**Signal**: `post_save` no modelo `Manifestation`

**Comportamento**:
- Escuta quando uma nova manifestação é criada (`created=True`)
- Dispara análise em thread separada (não trava o request HTTP)
- Thread é daemon (não impede encerramento do programa)

**Função**: `analyze_manifestation_async()`
- Executa `OpenAIService.analyze_manifestation()` em thread separada
- Trata erros sem quebrar o sistema

### 3. `intelligence/apps.py` - Registro de Signals

**Método**: `ready()`
- Importa os signals quando o app Django está pronto
- Garante que os signals sejam registrados corretamente

## Configuração

### Variáveis de Ambiente (.env)

```env
# OpenAI / IA
OPENAI_API_KEY=sk-...  # Sua chave da OpenAI
OPENAI_MODEL=gpt-4o-mini  # Modelo a usar (padrão: gpt-4o-mini)
NLP_ANALYSIS_VERSION=1.0  # Versão do algoritmo de análise
```

### Settings (`config/settings.py`)

```python
OPENAI_API_KEY = config('OPENAI_API_KEY', default='', cast=str)
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-4o-mini', cast=str)
NLP_ANALYSIS_VERSION = config('NLP_ANALYSIS_VERSION', default='1.0', cast=str)
```

## Prompt de Sistema

O sistema usa um prompt estruturado que instrui a IA a:

1. **Atuar como Analista Sênior de Gestão Pública**
2. **Extrair informações específicas**:
   - Sentimento (score numérico)
   - Urgência (nível 1-5)
   - Categoria sugerida
   - Resumo técnico
   - Palavras-chave
3. **Retornar APENAS JSON válido** (sem markdown, sem explicações)

## Modelo de Dados

### NLPAnalysis

Após a análise, os seguintes campos são preenchidos:

- `sentiment_score`: Float (-1.0 a 1.0)
- `urgency_level`: Integer (1 a 5)
- `suggested_category`: ForeignKey para ManifestationCategory (pode ser None)
- `keywords`: JSONField (lista de strings)
- `summary`: TextField (resumo técnico)
- `raw_ai_response`: JSONField (resposta completa da API para auditoria)
- `ai_model_used`: CharField (ex: "gpt-4o-mini")
- `analysis_version`: CharField (versão do algoritmo)

## Fluxo de Execução

1. **Cidadão cria manifestação** via API (`POST /api/v1/reports/manifestations/`)
2. **Manifestation é salva** no banco de dados
3. **Signal `post_save` é disparado**
4. **Thread assíncrona é iniciada** (não trava o response HTTP)
5. **OpenAIService analisa** a manifestação
6. **NLPAnalysis é criado/atualizado** com os resultados
7. **Response HTTP é retornado** ao cidadão (sem esperar a análise)

## Performance

### Assíncrono
- A análise é executada em thread separada
- O response HTTP não espera a conclusão da análise
- Cidadão recebe resposta imediata

### Tempo de Processamento
- Chamada à OpenAI: ~2-5 segundos
- Não impacta o tempo de resposta da API

### Escalabilidade Futura
- Para produção, recomenda-se migrar para **Celery** com Redis
- Permite processamento em workers separados
- Melhor controle de filas e retry

## Tratamento de Erros

### Cenários Tratados

1. **API Key não configurada**
   - Log: Warning
   - Ação: Retorna None, sistema continua funcionando

2. **Erro na chamada da API**
   - Log: Error com stack trace
   - Ação: Retorna None, manifestação é salva sem análise

3. **JSON inválido retornado**
   - Log: Error com resposta recebida
   - Ação: Retorna None, manifestação é salva sem análise

4. **Categoria sugerida não encontrada**
   - Log: Info
   - Ação: `suggested_category` fica como None

## Logs

O sistema registra logs em diferentes níveis:

- **INFO**: Início e conclusão de análises
- **WARNING**: API key não configurada
- **ERROR**: Erros na chamada da API ou parsing

**Exemplo de log**:
```
INFO: Nova manifestação criada: OUV-20240216-A3B4C. Disparando análise de IA em thread separada.
INFO: Iniciando análise de IA para manifestação OUV-20240216-A3B4C
INFO: Análise de IA concluída para manifestação OUV-20240216-A3B4C. Sentimento: -0.75, Urgência: 4
```

## Testes

### Teste Manual

1. Criar uma manifestação via API:
```bash
curl -X POST http://localhost:8000/api/v1/reports/manifestations/ \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Buraco enorme na rua principal causando acidentes. Muito perigoso!",
    "origin": "web"
  }'
```

2. Aguardar alguns segundos (2-5s)

3. Verificar análise criada:
```bash
curl http://localhost:8000/api/v1/reports/manifestations/{id}/
```

4. Verificar campo `nlp_analysis` no response JSON

### Verificar no Admin Django

1. Acessar: http://localhost:8000/admin/
2. Navegar para: Intelligence > NLP Analyses
3. Verificar análise criada com os dados extraídos

## Melhorias Futuras

1. **Celery Integration**: Migrar para Celery para melhor escalabilidade
2. **Retry Logic**: Implementar retry automático em caso de falha
3. **Cache**: Cachear análises similares para reduzir custos
4. **Múltiplos Provedores**: Suporte para outros LLMs (Claude, Gemini)
5. **Análise Incremental**: Re-analisar se descrição for atualizada
6. **Métricas**: Dashboard com estatísticas de análise
7. **Feedback Loop**: Permitir que gestores corrijam categorias sugeridas

## Custos

### Modelo: gpt-4o-mini
- Custo aproximado: ~$0.0001 por análise
- Tokens: ~500-1000 tokens por análise
- Ideal para MVP e desenvolvimento

### Modelo: gpt-4
- Custo aproximado: ~$0.01-0.02 por análise
- Maior precisão
- Recomendado para produção crítica

## Segurança

- ✅ API Key armazenada em variável de ambiente (não commitada)
- ✅ Tratamento de erros sem expor informações sensíveis
- ✅ Logs não incluem dados pessoais dos cidadãos
- ✅ Thread daemon não impede encerramento seguro

## Dependências

- `openai==1.12.0`: Cliente oficial da OpenAI
- `threading`: Biblioteca padrão Python para threads
- `logging`: Biblioteca padrão Python para logs

---

## Status: ✅ IMPLEMENTADO

O sistema está funcional e pronto para uso. Basta configurar a `OPENAI_API_KEY` no arquivo `.env`.
