# Estrutura de Diretórios - ProjectOuvidoria

## 📁 Árvore de Diretórios Completa

```
ProjectOuvidoria/
│
├── backend/                          # Backend Django
│   ├── config/                       # Configurações do Django
│   │   ├── __init__.py
│   │   ├── settings.py              # Configurações principais
│   │   ├── urls.py                  # URLs principais
│   │   ├── wsgi.py                  # WSGI config
│   │   └── asgi.py                  # ASGI config
│   │
│   ├── core/                        # App Core (Usuários, Autenticação)
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # Custom User Model
│   │   ├── views.py                 # Views/Endpoints
│   │   ├── urls.py                  # URLs do core
│   │   ├── admin.py                 # Admin Django
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── reports/                     # App de Manifestações
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # Manifestation, Attachment
│   │   ├── views.py                 # Views/Endpoints (futuro)
│   │   ├── urls.py                  # URLs do reports
│   │   ├── admin.py                 # Admin Django
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── intelligence/                # App de IA
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # SentimentAnalysis, Classification
│   │   ├── views.py                 # Views/Endpoints (futuro)
│   │   ├── urls.py                  # URLs do intelligence
│   │   ├── admin.py                 # Admin Django
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── integrations/                # App de Integrações
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # ExternalSystem
│   │   ├── views.py                 # Views/Endpoints (futuro)
│   │   ├── urls.py                  # URLs do integrations
│   │   ├── admin.py                 # Admin Django
│   │   └── migrations/
│   │       └── __init__.py
│   │
│   ├── manage.py                     # Django management script
│   ├── requirements.txt             # Dependências Python
│   ├── Dockerfile                   # Dockerfile do backend
│   ├── .dockerignore                # Arquivos ignorados no Docker
│   └── .env.example                 # Exemplo de variáveis de ambiente
│
├── frontend/                         # Frontend Vue.js
│   ├── public/                      # Arquivos públicos
│   │   └── manifest.json            # PWA manifest
│   │
│   ├── src/                         # Código fonte
│   │   ├── components/              # Componentes Vue (futuro)
│   │   │   └── atoms/               # Componentes atômicos (futuro)
│   │   │   └── molecules/           # Componentes moleculares (futuro)
│   │   │
│   │   ├── views/                   # Views/Páginas
│   │   │   └── HomeView.vue         # Página inicial
│   │   │
│   │   ├── services/                # Serviços
│   │   │   └── api.ts               # Cliente Axios configurado
│   │   │
│   │   ├── stores/                  # Stores Pinia
│   │   │   └── index.ts             # Placeholder
│   │   │
│   │   ├── router/                  # Vue Router
│   │   │   └── index.ts             # Configuração de rotas
│   │   │
│   │   ├── App.vue                  # Componente raiz
│   │   ├── main.ts                  # Entry point
│   │   ├── style.css                # Estilos globais
│   │   └── env.d.ts                 # Tipos TypeScript para env
│   │
│   ├── index.html                   # HTML principal
│   ├── package.json                 # Dependências Node
│   ├── vite.config.ts               # Configuração do Vite
│   ├── tsconfig.json                # Configuração TypeScript
│   ├── tsconfig.node.json           # TypeScript para Node
│   ├── .eslintrc.cjs                # Configuração ESLint
│   ├── Dockerfile                   # Dockerfile do frontend
│   ├── .dockerignore                # Arquivos ignorados no Docker
│   └── .env.example                 # Exemplo de variáveis de ambiente
│
├── docker-compose.yml               # Orquestração Docker
├── .gitignore                       # Arquivos ignorados no Git
├── README.md                        # Documentação principal
└── ESTRUTURA.md                     # Este arquivo
```

## 🎯 Organização por Domínio

### Backend (Django)

- **config/**: Configurações globais do Django
- **core/**: Funcionalidades centrais (usuários, autenticação, tenants)
- **reports/**: Domínio de negócio principal (manifestações, protocolos)
- **intelligence/**: Processamento de IA (classificação, sentimento)
- **integrations/**: Integrações com sistemas externos

### Frontend (Vue.js)

- **components/**: Componentes reutilizáveis (estrutura atomic design)
- **views/**: Páginas/rotas da aplicação
- **services/**: Comunicação com APIs externas
- **stores/**: Gerenciamento de estado (Pinia)
- **router/**: Configuração de rotas

## 🔄 Fluxo de Dados

```
Frontend (Vue.js) 
    ↓ HTTP/REST
Services (api.ts)
    ↓ Axios
Backend API (Django REST Framework)
    ↓ ORM
PostgreSQL Database
    ↓ Cache
Redis
```

## 📦 Serviços Docker

1. **db** (PostgreSQL 16): Banco de dados principal
2. **redis**: Cache e mensageria
3. **backend** (Django): API REST
4. **frontend** (Vue.js): Interface do usuário

## 🚀 Próximos Passos de Desenvolvimento

1. Implementar serializers e viewsets no backend
2. Criar componentes Vue no frontend
3. Implementar autenticação JWT completa
4. Adicionar testes unitários e de integração
5. Configurar CI/CD
6. Implementar funcionalidades de IA
7. Adicionar documentação da API (Swagger/OpenAPI)
