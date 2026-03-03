# 📋 Modelos Groq Disponíveis (2026)

## ⚠️ Modelo Descontinuado

O modelo `llama3-70b-8192` foi **descontinuado** pelo Groq e não está mais disponível.

## ✅ Modelos Recomendados

### 1. Llama 3.3 70B Versatile (Recomendado para Produção)
- **Nome**: `llama-3.3-70b-versatile`
- **Velocidade**: 280 tokens/segundo
- **Custo**: $0.59 input / $0.79 output por 1M tokens
- **Contexto**: 131K tokens
- **Uso**: Análises mais complexas e precisas

### 2. Llama 3.1 8B Instant (Recomendado para MVP/Desenvolvimento)
- **Nome**: `llama-3.1-8b-instant`
- **Velocidade**: 560 tokens/segundo (mais rápido)
- **Custo**: $0.05 input / $0.08 output por 1M tokens (mais barato)
- **Contexto**: 131K tokens
- **Uso**: Desenvolvimento e testes rápidos

## 🔧 Como Atualizar

### Opção 1: Llama 3.3 70B (Mais Poderoso)
Edite `backend/.env`:
```env
OPENAI_API_KEY=gsk_...
OPENAI_API_BASE=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
```

### Opção 2: Llama 3.1 8B (Mais Rápido e Barato)
Edite `backend/.env`:
```env
OPENAI_API_KEY=gsk_...
OPENAI_API_BASE=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
```

## 📊 Comparação

| Modelo | Velocidade | Custo | Precisão | Recomendado Para |
|--------|------------|-------|----------|------------------|
| llama-3.3-70b-versatile | 280 tok/s | $$ | Alta | Produção, análises complexas |
| llama-3.1-8b-instant | 560 tok/s | $ | Média-Alta | MVP, desenvolvimento, testes |

## 🔗 Referências

- [Groq Models Documentation](https://console.groq.com/docs/models)
- [Model Deprecations](https://console.groq.com/docs/deprecations)
