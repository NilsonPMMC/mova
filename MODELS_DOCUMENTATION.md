# 📊 Documentação dos Models - ProjectOuvidoria

## Estrutura Criada

### 1. Utils App - Modelo Base

#### `TimeStampedModel` (Abstract Base Class)
- **Localização**: `backend/utils/models.py`
- **Campos**:
  - `id`: UUIDField (PK) - Proteção contra ID enumeration attacks
  - `created_at`: DateTimeField (auto_now_add)
  - `updated_at`: DateTimeField (auto_now)
- **Uso**: Herdado por todos os models principais para auditoria automática

---

## 2. Reports App - Modelos de Negócio

### `ManifestationCategory`
**Tabela**: `manifestation_categories`

**Campos**:
- `id`: UUID (PK)
- `name`: CharField(200) - Nome da categoria
- `slug`: SlugField(200) - URL-friendly
- `is_active`: Boolean - Ativa/Inativa
- `sla_hours`: PositiveInteger - SLA em horas (padrão: 72h)
- `parent`: ForeignKey(self) - Suporte a hierarquia/subcategorias
- `description`: TextField - Descrição opcional
- `created_at`, `updated_at`: Timestamps automáticos

**Métodos**:
- `get_full_path()`: Retorna caminho completo incluindo pais (ex: "Infraestrutura > Pavimentação")

**Exemplo de uso**:
```python
categoria_pai = ManifestationCategory.objects.create(name="Infraestrutura")
subcategoria = ManifestationCategory.objects.create(
    name="Pavimentação",
    parent=categoria_pai
)
```

---

### `Manifestation` (Modelo Principal)
**Tabela**: `manifestations`

**Campos**:
- `id`: UUID (PK)
- `protocol`: CharField(50) - **Gerado automaticamente** no formato `OUV-YYYYMMDD-XXXXX`
- `citizen`: ForeignKey(User) - Cidadão que fez a manifestação (opcional)
- `description`: TextField - Relato do cidadão
- `status`: CharField - Choices:
  - `waiting_triage`: Aguardando Triagem
  - `in_analysis`: Em Análise
  - `forwarded`: Encaminhada
  - `resolved`: Resolvida
  - `closed`: Encerrada
- `origin`: CharField - Choices:
  - `app`: Aplicativo Mobile
  - `web`: Portal Web
  - `whatsapp`: WhatsApp
  - `phone`: Telefone
- `location_address`: CharField(500) - Endereço
- `latitude`: DecimalField(10,8) - Coordenada geográfica
- `longitude`: DecimalField(11,8) - Coordenada geográfica
- `is_anonymous`: Boolean - Manifestação anônima
- `category`: ForeignKey(ManifestationCategory) - Categoria atribuída
- `resolved_at`: DateTimeField - Data de resolução
- `resolved_by`: ForeignKey(User) - Quem resolveu
- `created_at`, `updated_at`: Timestamps automáticos

**Índices**:
- `protocol` (único)
- `status`
- `created_at`
- `latitude, longitude` (composto para queries geoespaciais)

**Métodos**:
- `generate_protocol()`: Gera protocolo único automaticamente
- `save()`: Sobrescrito para gerar protocolo se não existir

**Signal**:
- `pre_save`: Gera protocolo automaticamente antes de salvar

**Exemplo de uso**:
```python
manifestation = Manifestation.objects.create(
    description="Buraco na rua principal",
    origin=Manifestation.ORIGIN_WEB,
    location_address="Rua das Flores, 123",
    latitude=-23.5505,
    longitude=-46.6333,
    is_anonymous=False
)
# Protocolo gerado automaticamente: OUV-20240216-A3B4C
```

---

### `ManifestationUpdate` (Andamentos)
**Tabela**: `manifestation_updates`

**Campos**:
- `id`: UUID (PK)
- `manifestation`: ForeignKey(Manifestation) - Manifestação relacionada
- `internal_note`: TextField - Nota interna (visível apenas para equipe)
- `public_note`: TextField - Nota pública (visível ao cidadão)
- `new_status`: CharField - Novo status da manifestação
- `updated_by`: ForeignKey(User) - Quem fez a atualização
- `created_at`, `updated_at`: Timestamps automáticos

**Uso**: Rastreabilidade completa de todas as mudanças de status e notas adicionadas

**Exemplo de uso**:
```python
update = ManifestationUpdate.objects.create(
    manifestation=manifestation,
    new_status=Manifestation.STATUS_IN_ANALYSIS,
    public_note="Sua manifestação está sendo analisada pela equipe técnica.",
    internal_note="Encaminhar para o setor de obras públicas.",
    updated_by=user
)
```

---

### `Attachment` (Anexos)
**Tabela**: `attachments`

**Campos**:
- `id`: UUID (PK)
- `manifestation`: ForeignKey(Manifestation)
- `file`: FileField - Arquivo anexado
- `filename`: CharField(255) - Nome original do arquivo
- `file_size`: BigIntegerField - Tamanho em bytes
- `mime_type`: CharField(100) - Tipo MIME
- `uploaded_by`: ForeignKey(User) - Quem enviou
- `created_at`, `updated_at`: Timestamps automáticos

---

## 3. Intelligence App - Modelos de IA

### `NLPAnalysis` (Análise NLP/IA)
**Tabela**: `nlp_analyses`

**Campos**:
- `id`: UUID (PK)
- `manifestation`: OneToOneField(Manifestation) - Relacionamento 1:1
- `sentiment_score`: FloatField - Score de sentimento (-1.0 a +1.0)
- `urgency_level`: IntegerField - Nível de urgência (1 a 5)
- `suggested_category`: ForeignKey(ManifestationCategory) - Categoria sugerida pela IA
- `keywords`: JSONField - Lista de palavras-chave extraídas
- `summary`: TextField - Resumo gerado pela IA
- `raw_ai_response`: JSONField - Resposta completa da API de IA (auditoria)
- `ai_model_used`: CharField(100) - Modelo usado (ex: "gpt-4", "gpt-3.5-turbo")
- `analysis_version`: CharField(20) - Versão do algoritmo/pipeline
- `analyzed_at`: DateTimeField - Data da análise
- `created_at`, `updated_at`: Timestamps automáticos

**Índices**:
- `sentiment_score`
- `urgency_level`
- `analyzed_at`

**Métodos**:
- `get_sentiment_label()`: Retorna label do sentimento (Positivo/Negativo/Neutro)
- `get_urgency_label()`: Retorna label da urgência (Muito Baixa a Crítica)

**Exemplo de uso**:
```python
analysis = NLPAnalysis.objects.create(
    manifestation=manifestation,
    sentiment_score=-0.75,  # Negativo
    urgency_level=4,  # Alta urgência
    suggested_category=categoria_infraestrutura,
    keywords=["buraco", "rua", "perigo", "acidente"],
    summary="Manifestação sobre buraco na rua que representa risco de acidente.",
    ai_model_used="gpt-4",
    raw_ai_response={
        "model": "gpt-4",
        "choices": [...],
        "usage": {...}
    }
)
```

---

## Relacionamentos entre Models

```
ManifestationCategory (pode ter parent)
    ↓ (1:N)
Manifestation
    ↓ (1:1)
NLPAnalysis
    ↓ (1:N)
ManifestationUpdate
    ↓ (1:N)
Attachment
```

---

## Migrations Criadas

1. **utils**: Não requer migration (modelo abstrato)
2. **reports**: `0001_initial.py`
   - ManifestationCategory
   - Manifestation (com índices)
   - ManifestationUpdate
   - Attachment
3. **intelligence**: `0001_initial.py`
   - NLPAnalysis (com índices)

---

## Segurança e Boas Práticas

✅ **UUID como PK**: Proteção contra ID enumeration attacks  
✅ **TimeStampedModel**: Auditoria automática (created_at/updated_at)  
✅ **Índices otimizados**: Performance em queries frequentes  
✅ **Geração automática de protocolo**: Garantia de unicidade  
✅ **JSONField para dados estruturados**: Flexibilidade para evolução  
✅ **ForeignKeys com SET_NULL**: Preservação de dados históricos  

---

## Próximos Passos

1. ✅ Models criados
2. ✅ Migrations aplicadas
3. ⏭️ Criar Serializers (DRF)
4. ⏭️ Criar ViewSets/Views
5. ⏭️ Implementar lógica de geração de protocolo
6. ⏭️ Integrar com APIs de IA (OpenAI, etc.)
7. ⏭️ Criar testes unitários
