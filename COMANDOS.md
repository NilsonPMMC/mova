# 📋 Lista Completa de Comandos - ProjectOuvidoria

## 🐳 Docker Compose

### Inicialização e Build

```bash
# Construir todas as imagens (primeira vez ou após mudanças)
docker compose build

# Construir apenas o backend
docker compose build backend

# Construir apenas o frontend
docker compose build frontend

# Construir sem usar cache (força rebuild completo)
docker compose build --no-cache backend
```

### Iniciar e Parar Serviços

```bash
# Iniciar todos os serviços em background
docker compose up -d

# Iniciar todos os serviços (com logs no terminal)
docker compose up

# Parar todos os serviços
docker compose stop

# Parar e remover containers
docker compose down

# Parar, remover containers e volumes (⚠️ APAGA DADOS)
docker compose down -v

# Reiniciar um serviço específico
docker compose restart backend
docker compose restart frontend
docker compose restart db
docker compose restart redis
```

### Logs e Monitoramento

```bash
# Ver logs de todos os serviços
docker compose logs

# Ver logs do backend (últimas 100 linhas)
docker compose logs --tail=100 backend

# Seguir logs em tempo real
docker compose logs -f backend

# Ver logs do frontend
docker compose logs -f frontend

# Ver status dos containers
docker compose ps

# Ver uso de recursos
docker stats
```

### Executar Comandos Dentro dos Containers

```bash
# Executar comando no backend
docker compose exec backend <comando>

# Executar comando no frontend
docker compose exec frontend <comando>

# Executar comando no banco de dados
docker compose exec db <comando>

# Abrir shell interativo no backend
docker compose exec backend bash

# Abrir shell interativo no frontend
docker compose exec frontend sh
```

---

## 🐍 Django - Backend

### Migrações

```bash
# Criar migrações (após alterar models)
docker compose exec backend python manage.py makemigrations

# Aplicar migrações
docker compose exec backend python manage.py migrate

# Ver status das migrações
docker compose exec backend python manage.py showmigrations

# Reverter última migração
docker compose exec backend python manage.py migrate <app_name> <migration_number>

# Aplicar migrações de um app específico
docker compose exec backend python manage.py migrate core
docker compose exec backend python manage.py migrate reports
```

### Django Admin e Usuários

```bash
# Criar superusuário
docker compose exec backend python manage.py createsuperuser

# Alterar senha de usuário
docker compose exec backend python manage.py changepassword <username>

# Abrir shell do Django
docker compose exec backend python manage.py shell
```

### Comandos de Gestão Personalizados

```bash
# Popular sistema com dados de teste
docker compose exec backend python manage.py populate_system

# Popular sistema limpando dados anteriores
docker compose exec backend python manage.py populate_system --clean

# Testar busca vetorial com Google Gemini
docker compose exec backend python manage.py testar_gemini

# Testar busca vetorial com OpenAI (se ainda existir)
docker compose exec backend python manage.py testar_api

# Seed de categorias
docker compose exec backend python manage.py seed_categories
```

### Desenvolvimento e Debug

```bash
# Rodar servidor de desenvolvimento (já roda automaticamente no docker-compose)
docker compose exec backend python manage.py runserver 0.0.0.0:8000

# Verificar configurações
docker compose exec backend python manage.py check

# Coletar arquivos estáticos
docker compose exec backend python manage.py collectstatic --noinput

# Limpar cache
docker compose exec backend python manage.py clear_cache
```

### Testes

```bash
# Rodar todos os testes
docker compose exec backend python manage.py test

# Rodar testes de um app específico
docker compose exec backend python manage.py test core
docker compose exec backend python manage.py test reports
docker compose exec backend python manage.py test intelligence

# Rodar testes com verbosidade
docker compose exec backend python manage.py test --verbosity=2

# Rodar testes específicos
docker compose exec backend python manage.py test reports.tests.test_models
```

---

## 🗄️ Banco de Dados PostgreSQL

### Acesso e Consultas

```bash
# Conectar ao PostgreSQL via psql
docker compose exec db psql -U postgres -d projectouvidoria

# Executar comando SQL direto
docker compose exec db psql -U postgres -d projectouvidoria -c "SELECT * FROM users;"

# Listar todas as tabelas
docker compose exec db psql -U postgres -d projectouvidoria -c "\dt"

# Listar extensões instaladas
docker compose exec db psql -U postgres -d projectouvidoria -c "\dx"

# Verificar se pgvector está instalado
docker compose exec db psql -U postgres -d projectouvidoria -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Backup do banco de dados
docker compose exec db pg_dump -U postgres projectouvidoria > backup.sql

# Restaurar backup
docker compose exec -T db psql -U postgres projectouvidoria < backup.sql
```

### Limpeza

```bash
# Limpar todas as tabelas (⚠️ CUIDADO)
docker compose exec db psql -U postgres -d projectouvidoria -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Resetar banco (deleta e recria)
docker compose down -v
docker compose up -d db
docker compose exec backend python manage.py migrate
```

---

## 🔴 Redis

```bash
# Conectar ao Redis CLI
docker compose exec redis redis-cli

# Verificar se Redis está funcionando
docker compose exec redis redis-cli ping

# Limpar todo o cache do Redis
docker compose exec redis redis-cli FLUSHALL

# Ver informações do Redis
docker compose exec redis redis-cli INFO

# Ver chaves armazenadas
docker compose exec redis redis-cli KEYS "*"
```

---

## 🎨 Frontend (Vue.js)

```bash
# Instalar dependências (se necessário)
docker compose exec frontend npm install

# Rodar servidor de desenvolvimento (já roda automaticamente)
docker compose exec frontend npm run dev

# Build para produção
docker compose exec frontend npm run build

# Verificar lint
docker compose exec frontend npm run lint

# Formatar código
docker compose exec frontend npm run format
```

---

## 🧹 Limpeza e Manutenção

### Docker

```bash
# Remover containers parados
docker container prune

# Remover imagens não utilizadas
docker image prune

# Remover volumes não utilizados
docker volume prune

# Limpeza completa (⚠️ Remove tudo não utilizado)
docker system prune -a --volumes

# Ver uso de disco
docker system df
```

### Projeto

```bash
# Limpar arquivos Python compilados
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Limpar arquivos de migração locais (se necessário recriar)
# ⚠️ CUIDADO: Não faça isso em produção!
# rm backend/*/migrations/0*.py
```

---

## 🚀 Setup Inicial (Primeira Vez)

```bash
# 1. Clonar repositório (se aplicável)
# git clone <repo-url>
# cd ProjectOuvidoria

# 2. Copiar arquivo .env de exemplo (se existir)
# cp backend/.env.example backend/.env

# 3. Editar backend/.env e adicionar:
#    - GEMINI_API_KEY (obter em https://makersuite.google.com/app/apikey)
#    - Outras variáveis necessárias

# 4. Construir imagens
docker compose build

# 5. Iniciar serviços
docker compose up -d

# 6. Aguardar serviços ficarem saudáveis
docker compose ps

# 7. Aplicar migrações
docker compose exec backend python manage.py migrate

# 8. Criar superusuário
docker compose exec backend python manage.py createsuperuser

# 9. Popular dados de teste (opcional)
docker compose exec backend python manage.py populate_system

# 10. Acessar aplicação
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Django Admin: http://localhost:8000/admin
```

---

## 🔧 Troubleshooting

### Backend não inicia

```bash
# Ver logs de erro
docker compose logs backend

# Verificar se banco está saudável
docker compose ps db

# Tentar rebuild
docker compose build --no-cache backend
docker compose up -d backend
```

### Banco de dados com problemas

```bash
# Ver logs do banco
docker compose logs db

# Verificar conexão
docker compose exec db psql -U postgres -c "SELECT version();"

# Resetar banco completamente
docker compose down -v
docker compose up -d db
# Aguardar banco ficar saudável
docker compose exec backend python manage.py migrate
```

### Frontend não carrega

```bash
# Ver logs
docker compose logs frontend

# Reinstalar dependências
docker compose exec frontend rm -rf node_modules
docker compose exec frontend npm install

# Rebuild
docker compose build --no-cache frontend
docker compose restart frontend
```

### Portas já em uso

```bash
# Ver o que está usando as portas
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Parar serviços conflitantes ou alterar portas no docker-compose.yml
```

---

## 📝 Comandos Úteis Combinados

```bash
# Rebuild completo e restart
docker compose build && docker compose down && docker compose up -d

# Ver logs de todos os serviços em tempo real
docker compose logs -f

# Executar migrações e popular dados
docker compose exec backend python manage.py migrate && docker compose exec backend python manage.py populate_system

# Backup completo (banco + volumes)
docker compose exec db pg_dump -U postgres projectouvidoria > backup_$(date +%Y%m%d_%H%M%S).sql

# Limpar tudo e começar do zero
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

---

## 🔐 Variáveis de Ambiente Importantes

Certifique-se de ter no `backend/.env`:

```env
# Banco de Dados
DB_NAME=projectouvidoria
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Google Gemini (para Embeddings)
GEMINI_API_KEY=your-key-here

# OpenAI/Groq (para LLM)
OPENAI_API_KEY=your-key-here
OPENAI_API_BASE=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
```

---

## 📚 URLs Importantes

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/v1
- **Django Admin**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/v1/docs (se configurado)

---

## 🎯 Comandos Mais Usados (Quick Reference)

```bash
# Desenvolvimento diário
docker compose up -d                    # Iniciar tudo
docker compose logs -f backend          # Ver logs
docker compose exec backend python manage.py migrate  # Migrar
docker compose exec backend python manage.py testar_gemini  # Testar IA

# Quando mudar código
docker compose restart backend          # Reiniciar backend
docker compose restart frontend         # Reiniciar frontend

# Quando mudar dependências
docker compose build backend            # Rebuild backend
docker compose build frontend          # Rebuild frontend
docker compose restart                 # Reiniciar tudo
```

---

**Última atualização**: 2026-02-17
**Versão do projeto**: ProjectOuvidoria v1.0
