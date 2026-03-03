# 🎨 Humanização do Fluxo - ProjectOuvidoria

## Mudanças Implementadas

### Backend

#### 1. Modelo User Atualizado (`core/models.py`)
- ✅ Campo `cpf`: CharField único e indexado
- ✅ Campo `full_name`: Nome completo do usuário
- ✅ Campo `is_temporary`: Flag para usuários criados automaticamente
- ✅ Campo `email`: Agora pode ser null (para usuários temporários)

#### 2. Serializer Atualizado (`reports/serializers.py`)
- ✅ `ManifestationCreateSerializer` agora aceita:
  - `citizen_name`: Nome do cidadão (opcional)
  - `citizen_email`: Email do cidadão (opcional)
  - `citizen_cpf`: CPF do cidadão (opcional)
- ✅ Lógica de Soft Auth:
  - Busca usuário existente por CPF ou Email
  - Se não encontrar, cria usuário temporário automaticamente
  - Vincula manifestação ao usuário criado/encontrado

#### 3. View Atualizada (`reports/views.py`)
- ✅ Action `by_protocol`: Endpoint público para buscar manifestação por protocolo
- ✅ Permite que cidadão acompanhe sua manifestação sem autenticação

#### 4. Seed de Categorias (`reports/management/commands/seed_categories.py`)
- ✅ Comando: `python manage.py seed_categories`
- ✅ Categorias criadas com SLAs reais:
  - Iluminação Pública: 48h
  - Buraco em Via/Pavimentação: 120h
  - Saúde/Falta de Médico: 24h
  - Coleta de Lixo: 24h
  - Zeladoria: 72h
  - Trânsito: 48h
  - Segurança: 12h
  - Meio Ambiente: 96h

### Frontend

#### 1. Store Atualizada (`stores/manifestation.ts`)
- ✅ Campos adicionados: `citizenName`, `citizenEmail`, `citizenCpf`
- ✅ Método `setCitizenData()` para definir dados do cidadão
- ✅ Payload de envio inclui dados do cidadão (se não anônimo)

#### 2. Novo Componente: `StepIdentification.vue`
- ✅ Passo de identificação do cidadão
- ✅ Campos: Nome, Email ou CPF
- ✅ Botão "Prefiro continuar anônimo"
- ✅ Validação automática (email vs CPF)

#### 3. Novo Componente: `StepSuccess.vue`
- ✅ Recibo de Compromisso completo
- ✅ Mostra categoria sugerida pela IA
- ✅ Mostra SLA estimado da categoria
- ✅ Polling a cada 2s para atualizar análise NLP
- ✅ Exibe urgência e sentimento quando disponível
- ✅ Design visual rico com ícones e cores

#### 4. View Atualizada (`views/NewManifestation.vue`)
- ✅ Novo fluxo com 6 passos:
  1. Boas-vindas
  2. **Identificação** (NOVO)
  3. Descrição
  4. Localização
  5. Revisão
  6. Sucesso (melhorado)

## Fluxo Completo

```
1. Boas-vindas
   ↓
2. Identificação (Nome + Email/CPF ou Anônimo)
   ↓
3. Descrição do Problema
   ↓
4. Localização (GPS ou Manual)
   ↓
5. Revisão
   ↓
6. Envio → API
   ↓
7. Sucesso com Recibo:
   - Protocolo
   - Categoria (quando IA processar)
   - SLA Estimado
   - Urgência e Sentimento (quando disponível)
```

## Endpoints Novos

### Buscar por Protocolo (Público)
```
GET /api/v1/reports/manifestations/by-protocol/{protocol}/
```
Permite que cidadão acompanhe sua manifestação usando apenas o protocolo.

## Comandos Úteis

### Popular Categorias
```bash
docker-compose exec backend python manage.py seed_categories
```

### Criar Migrations
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

## Melhorias de UX

✅ **Humanização**: Cidadão pode se identificar (não é mais 100% anônimo)  
✅ **Transparência**: SLA visível logo após categoria ser definida  
✅ **Feedback Visual**: Recibo rico com ícones e cores  
✅ **Polling Inteligente**: Atualiza automaticamente quando IA processa  
✅ **Soft Auth**: Cria usuário automaticamente sem complicar o fluxo  

## Próximos Passos Sugeridos

1. ⏭️ Adicionar notificações por email quando categoria for definida
2. ⏭️ Criar página de acompanhamento por protocolo
3. ⏭️ Adicionar QR Code no recibo para fácil acesso
4. ⏭️ Implementar histórico de manifestações do cidadão
5. ⏭️ Adicionar upload de fotos no passo de descrição

---

## Status: ✅ IMPLEMENTADO

O fluxo está humanizado e pronto para uso! 🎉
