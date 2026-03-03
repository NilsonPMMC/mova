# ProjectOuvidoria

Plataforma de Ouvidoria moderna, escalável e baseada em dados para gestão pública.

## 🏗️ Arquitetura

### Stack Tecnológico

- **Backend**: Python 3.12+ com Django 5.x e Django Rest Framework (DRF)
- **Frontend**: Vue.js 3 (Composition API) com Vite e TypeScript
- **Banco de Dados**: PostgreSQL 16
- **Cache/Mensageria**: Redis
- **Infraestrutura**: Docker e Docker Compose

### Estrutura do Projeto

```
ProjectOuvidoria/
├── backend/                 # Aplicação Django
│   ├── config/             # Configurações do Django
│   ├── core/               # App core (User Model, Autenticação)
│   ├── reports/            # App de manifestações/protocolos
│   ├── intelligence/       # App de IA (classificação, sentimento)
│   ├── integrations/       # App de integrações externas
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Aplicação Vue.js
│   ├── src/
│   │   ├── components/    # Componentes Vue
│   │   ├── views/         # Views/Páginas
│   │   ├── services/      # Serviços de API
│   │   ├── stores/        # Stores Pinia
│   │   ├── router/        # Configuração do Vue Router
│   │   └── main.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml      # Orquestração dos serviços
└── README.md
```

## 🚀 Início Rápido

### Pré-requisitos

- Docker e Docker Compose instalados
- Git

### Configuração Inicial

1. **Clone o repositório** (se aplicável)

2. **Configure as variáveis de ambiente**

   Copie os arquivos `.env.example` para `.env`:

   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

   Edite os arquivos `.env` conforme necessário.

3. **Inicie os serviços com Docker Compose**

   ```bash
   docker-compose up --build
   ```

   Ou em modo detached:

   ```bash
   docker-compose up -d --build
   ```

4. **Acesse as aplicações**

   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Admin Django: http://localhost:8000/admin
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

### Criar Superusuário (Django Admin)

```bash
docker-compose exec backend python manage.py createsuperuser
```

## 📋 Apps Django

### Core
- Custom User Model
- Autenticação e autorização
- Gestão de tenants/prefeituras (futuro)

### Reports
- Manifestações/Denúncias
- Protocolos
- Anexos

### Intelligence
- Análise de sentimento
- Classificação automática de manifestações
- Integração com modelos de IA

### Integrations
- Conexões com sistemas legados
- APIs externas
- Webhooks

## 🔧 Desenvolvimento

### Backend

```bash
# Entrar no container do backend
docker-compose exec backend bash

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic
```

### Frontend

```bash
# Entrar no container do frontend
docker-compose exec frontend sh

# Instalar dependências (se necessário)
npm install

# Executar em desenvolvimento
npm run dev
```

## 📝 Variáveis de Ambiente

### Backend (.env)

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DB_NAME=projectouvidoria
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 🐳 Comandos Docker Úteis

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (⚠️ apaga dados)
docker-compose down -v

# Ver logs
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend

# Reconstruir um serviço específico
docker-compose build backend

# Executar comandos no backend
docker-compose exec backend python manage.py <comando>
```

## 📚 Próximos Passos

- [ ] Implementar autenticação JWT completa
- [ ] Criar endpoints da API REST
- [ ] Implementar interface de usuário
- [ ] Configurar CI/CD
- [ ] Adicionar testes automatizados
- [ ] Implementar funcionalidades de IA
- [ ] Configurar monitoramento e logging

## 🤝 Contribuindo

Este é um projeto em desenvolvimento inicial. Contribuições são bem-vindas!

## 📄 Licença

[Definir licença]
