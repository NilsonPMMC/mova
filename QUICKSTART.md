# 🚀 Guia de Início Rápido - ProjectOuvidoria

## Pré-requisitos

- Docker Desktop instalado e rodando
- Git (opcional)

## Passo a Passo

### 1. Configurar Variáveis de Ambiente

Copie os arquivos de exemplo:

```bash
# Windows PowerShell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env

# Linux/Mac
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Iniciar os Serviços

```bash
docker-compose up --build
```

Este comando irá:
- Construir as imagens Docker
- Iniciar PostgreSQL, Redis, Backend e Frontend
- Executar as migrações do Django automaticamente

### 3. Acessar as Aplicações

Após alguns minutos (quando todos os serviços estiverem prontos):

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/v1/health/
- **Admin Django**: http://localhost:8000/admin

### 4. Criar Superusuário (Opcional)

Para acessar o admin do Django:

```bash
docker-compose exec backend python manage.py createsuperuser
```

Siga as instruções para criar um usuário admin.

## Verificar Status dos Serviços

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Ver status dos containers
docker-compose ps
```

## Comandos Úteis

### Parar os Serviços

```bash
docker-compose down
```

### Parar e Remover Volumes (⚠️ Apaga dados)

```bash
docker-compose down -v
```

### Reconstruir um Serviço Específico

```bash
docker-compose build backend
docker-compose up -d backend
```

### Executar Comandos no Backend

```bash
# Criar migrações
docker-compose exec backend python manage.py makemigrations

# Aplicar migrações
docker-compose exec backend python manage.py migrate

# Shell do Django
docker-compose exec backend python manage.py shell

# Coletar arquivos estáticos
docker-compose exec backend python manage.py collectstatic
```

### Executar Comandos no Frontend

```bash
# Instalar novas dependências
docker-compose exec frontend npm install <pacote>

# Executar lint
docker-compose exec frontend npm run lint
```

## Troubleshooting

### Porta já em uso

Se alguma porta estiver em uso, edite o `docker-compose.yml` para alterar as portas mapeadas.

### Erro de conexão com o banco

Aguarde alguns segundos após iniciar os serviços. O PostgreSQL precisa de tempo para inicializar.

### Erro de permissão

No Windows, certifique-se de que o Docker Desktop está rodando e tem permissões adequadas.

### Limpar tudo e começar do zero

```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Estrutura de URLs da API

- `GET /api/v1/health/` - Health check do backend
- `GET /api/v1/reports/` - Listar manifestações (futuro)
- `GET /api/v1/intelligence/` - Endpoints de IA (futuro)
- `GET /api/v1/integrations/` - Endpoints de integração (futuro)

## Próximos Passos

1. ✅ Ambiente configurado e rodando
2. ⏭️ Criar endpoints da API REST
3. ⏭️ Implementar interface do usuário
4. ⏭️ Adicionar autenticação JWT
5. ⏭️ Implementar funcionalidades de IA
