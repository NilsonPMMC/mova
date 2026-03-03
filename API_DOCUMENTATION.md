# 📡 Documentação da API REST - ProjectOuvidoria

## Endpoints Disponíveis

### Base URL
```
http://localhost:8000/api/v1/
```

---

## 📋 Manifestações

### 1. Criar Manifestação (Público - AllowAny)
**POST** `/api/v1/reports/manifestations/`

**Permissão**: `AllowAny` (qualquer pessoa pode criar)

**Body**:
```json
{
  "description": "Buraco na rua principal causando acidentes",
  "category": "uuid-da-categoria",  // Opcional
  "location_address": "Rua das Flores, 123",
  "latitude": -23.5505,  // Opcional, mas se fornecido, longitude também deve ser
  "longitude": -46.6333,  // Opcional, mas se fornecido, latitude também deve ser
  "is_anonymous": false,
  "origin": "web"  // Opcional: "app", "web", "whatsapp", "phone"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "protocol": "OUV-20240216-A3B4C",
  "description": "Buraco na rua principal...",
  "status": "waiting_triage",
  "status_display": "Aguardando Triagem",
  "nlp_analysis": null,
  "updates": [],
  "attachments": [],
  "created_at": "2026-02-16T14:30:00Z",
  ...
}
```

---

### 2. Listar Manifestações (Autenticado)
**GET** `/api/v1/reports/manifestations/`

**Permissão**: `IsAuthenticated`

**Query Parameters**:
- `status`: Filtrar por status (`waiting_triage`, `in_analysis`, etc.)
- `category`: Filtrar por categoria (UUID)
- `origin`: Filtrar por origem (`app`, `web`, `whatsapp`, `phone`)
- `search`: Buscar por protocolo, descrição ou endereço
- `ordering`: Ordenação (`-created_at`, `status`, etc.)

**Exemplo**:
```
GET /api/v1/reports/manifestations/?status=waiting_triage&search=buraco
```

**Response** (200 OK):
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/v1/reports/manifestations/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "protocol": "OUV-20240216-A3B4C",
      "description": "Buraco na rua...",
      "status": "waiting_triage",
      "status_display": "Aguardando Triagem",
      "category_name": "Infraestrutura",
      "citizen_name": "João Silva",
      "is_anonymous": false,
      "created_at": "2026-02-16T14:30:00Z",
      "has_nlp_analysis": false
    }
  ]
}
```

---

### 3. Detalhes da Manifestação (Autenticado)
**GET** `/api/v1/reports/manifestations/{id}/`

**Permissão**: `IsAuthenticated`

**Response** (200 OK):
```json
{
  "id": "uuid",
  "protocol": "OUV-20240216-A3B4C",
  "citizen": "user-uuid",
  "citizen_name": "João Silva",
  "description": "Buraco na rua principal...",
  "status": "in_analysis",
  "status_display": "Em Análise",
  "origin": "web",
  "origin_display": "Portal Web",
  "location_address": "Rua das Flores, 123",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "is_anonymous": false,
  "category": "category-uuid",
  "category_detail": {
    "id": "uuid",
    "name": "Infraestrutura",
    "slug": "infraestrutura",
    "full_path": "Infraestrutura",
    "sla_hours": 72,
    "is_active": true
  },
  "resolved_at": null,
  "resolved_by": null,
  "resolved_by_name": null,
  "created_at": "2026-02-16T14:30:00Z",
  "updated_at": "2026-02-16T14:35:00Z",
  "nlp_analysis": {
    "id": "uuid",
    "sentiment_score": -0.75,
    "sentiment_label": "Negativo",
    "urgency_level": 4,
    "urgency_label": "Alta",
    "suggested_category": "category-uuid",
    "suggested_category_name": "Infraestrutura",
    "keywords": ["buraco", "rua", "perigo", "acidente"],
    "summary": "Manifestação sobre buraco na rua que representa risco de acidente.",
    "ai_model_used": "gpt-4",
    "analysis_version": "1.0",
    "analyzed_at": "2026-02-16T14:31:00Z"
  },
  "updates": [
    {
      "id": "uuid",
      "internal_note": "Encaminhar para obras públicas",
      "public_note": "Sua manifestação está sendo analisada.",
      "new_status": "in_analysis",
      "new_status_display": "Em Análise",
      "updated_by": "user-uuid",
      "updated_by_name": "Maria Santos",
      "created_at": "2026-02-16T14:35:00Z"
    }
  ],
  "attachments": []
}
```

---

### 4. Atualizar Manifestação (Autenticado)
**PUT/PATCH** `/api/v1/reports/manifestations/{id}/`

**Permissão**: `IsAuthenticated`

**Body** (campos opcionais):
```json
{
  "status": "in_analysis",
  "category": "category-uuid",
  "resolved_by": "user-uuid"
}
```

---

### 5. Adicionar Andamento (Autenticado)
**POST** `/api/v1/reports/manifestations/{id}/add_update/`

**Permissão**: `IsAuthenticated`

**Body**:
```json
{
  "internal_note": "Nota interna para equipe",
  "public_note": "Nota pública visível ao cidadão",
  "new_status": "in_analysis"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "internal_note": "Nota interna para equipe",
  "public_note": "Nota pública visível ao cidadão",
  "new_status": "in_analysis",
  "new_status_display": "Em Análise",
  "updated_by": "user-uuid",
  "updated_by_name": "Maria Santos",
  "created_at": "2026-02-16T14:40:00Z"
}
```

**Nota**: O status da manifestação é atualizado automaticamente se `new_status` for fornecido.

---

### 6. Resolver Manifestação (Autenticado)
**POST** `/api/v1/reports/manifestations/{id}/resolve/`

**Permissão**: `IsAuthenticated`

**Response** (200 OK): Retorna a manifestação atualizada com `status: "resolved"` e `resolved_at` preenchido.

---

### 7. Encerrar Manifestação (Autenticado)
**POST** `/api/v1/reports/manifestations/{id}/close/`

**Permissão**: `IsAuthenticated`

**Response** (200 OK): Retorna a manifestação atualizada com `status: "closed"`.

---

## 📂 Categorias

### 1. Listar Categorias (Público)
**GET** `/api/v1/reports/categories/`

**Permissão**: `AllowAny`

**Query Parameters**:
- `parent`: Filtrar subcategorias de uma categoria pai (UUID)

**Exemplo**:
```
GET /api/v1/reports/categories/?parent=uuid-da-categoria-pai
```

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "name": "Infraestrutura",
    "slug": "infraestrutura",
    "full_path": "Infraestrutura",
    "sla_hours": 72,
    "is_active": true
  },
  {
    "id": "uuid",
    "name": "Pavimentação",
    "slug": "pavimentacao",
    "full_path": "Infraestrutura > Pavimentação",
    "sla_hours": 48,
    "is_active": true
  }
]
```

---

### 2. Detalhes da Categoria (Público)
**GET** `/api/v1/reports/categories/{id}/`

**Permissão**: `AllowAny`

---

## 🔐 Autenticação

Atualmente, a API usa autenticação básica do Django REST Framework. Para requisições autenticadas, inclua o header:

```
Authorization: Token seu-token-aqui
```

Ou para JWT (quando implementado):
```
Authorization: Bearer seu-jwt-token-aqui
```

---

## 📊 Serializers Utilizados

### Para Criação (POST)
- **ManifestationCreateSerializer**: Campos limitados, protocolo/status gerados automaticamente

### Para Listagem (GET list)
- **ManifestationListSerializer**: Campos simplificados para performance

### Para Detalhes (GET detail, PUT, PATCH)
- **ManifestationDetailSerializer**: Todos os campos + nested `nlp_analysis`, `updates`, `attachments`

---

## 🎯 Permissões

| Endpoint | Método | Permissão |
|----------|--------|-----------|
| `/manifestations/` | POST | `AllowAny` |
| `/manifestations/` | GET | `IsAuthenticated` |
| `/manifestations/{id}/` | GET | `IsAuthenticated` |
| `/manifestations/{id}/` | PUT/PATCH | `IsAuthenticated` |
| `/manifestations/{id}/` | DELETE | `IsAuthenticated` |
| `/manifestations/{id}/add_update/` | POST | `IsAuthenticated` |
| `/manifestations/{id}/resolve/` | POST | `IsAuthenticated` |
| `/manifestations/{id}/close/` | POST | `IsAuthenticated` |
| `/categories/` | GET | `AllowAny` |

---

## 🧪 Exemplos de Uso

### Criar Manifestação (cidadão anônimo)
```bash
curl -X POST http://localhost:8000/api/v1/reports/manifestations/ \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Buraco na rua",
    "location_address": "Rua das Flores, 123",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "is_anonymous": false,
    "origin": "web"
  }'
```

### Listar Manifestações (funcionário autenticado)
```bash
curl -X GET http://localhost:8000/api/v1/reports/manifestations/ \
  -H "Authorization: Token seu-token"
```

### Adicionar Andamento
```bash
curl -X POST http://localhost:8000/api/v1/reports/manifestations/{id}/add_update/ \
  -H "Authorization: Token seu-token" \
  -H "Content-Type: application/json" \
  -d '{
    "public_note": "Sua manifestação está sendo analisada.",
    "new_status": "in_analysis"
  }'
```

---

## 📝 Notas Importantes

1. **Protocolo**: Gerado automaticamente no formato `OUV-YYYYMMDD-XXXXX`
2. **Status Inicial**: Sempre `waiting_triage` ao criar
3. **NLP Analysis**: Pode ser `null` se ainda não foi processada pela IA
4. **Cidadão Anônimo**: Se `is_anonymous=true`, `citizen` e `citizen_name` serão `null`
5. **Validação de Coordenadas**: Se `latitude` fornecida, `longitude` também deve ser (e vice-versa)
