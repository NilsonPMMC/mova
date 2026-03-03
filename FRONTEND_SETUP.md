# 🎨 Setup do Frontend - Interface Conversacional

## Instalação de Dependências

Execute no container do frontend ou localmente:

```bash
# No container
docker-compose exec frontend npm install

# Ou localmente
cd frontend
npm install
```

## Dependências Adicionadas

- **tailwindcss**: Framework CSS utility-first
- **postcss**: Processador CSS
- **autoprefixer**: Adiciona prefixos CSS automaticamente
- **lucide-vue-next**: Biblioteca de ícones moderna

## Estrutura Criada

### Stores (Pinia)
- `src/stores/manifestation.ts` - Gerenciamento de estado do formulário

### Componentes
- `src/components/ChatBubble.vue` - Bolha de chat (bot/usuário)
- `src/components/StepDescription.vue` - Campo de descrição expansível
- `src/components/StepLocation.vue` - Geolocalização e endereço manual
- `src/components/StepReview.vue` - Revisão antes de enviar

### Views
- `src/views/NewManifestation.vue` - Fluxo wizard completo
- `src/views/HomeView.vue` - Página inicial atualizada

### Configurações
- `tailwind.config.js` - Configuração do Tailwind com cores GovTech
- `postcss.config.js` - Configuração do PostCSS
- `src/style.css` - Estilos globais com Tailwind

## Fluxo da Interface

1. **Boas-vindas**: Mensagem inicial da IA
2. **Descrição**: Campo de texto expansível para o problema
3. **Localização**: Botão de geolocalização + campo manual
4. **Revisão**: Resumo antes de enviar
5. **Sucesso**: Protocolo gerado + status de análise

## Características UX

✅ **Mobile-First**: Design responsivo otimizado para celular  
✅ **Animações Suaves**: Fade-in e slide-up entre etapas  
✅ **Feedback Visual**: Estados de loading, sucesso e erro  
✅ **Geolocalização**: Integração com API do navegador  
✅ **Auto-expand**: Textarea que cresce automaticamente  
✅ **Cores GovTech**: Azul institucional (#0066cc)  

## Acessar

Após instalar as dependências e reiniciar o frontend:

```
http://localhost:5173/nova-manifestacao
```

## Próximos Passos

1. Instalar dependências: `npm install`
2. Reiniciar frontend: `docker-compose restart frontend`
3. Testar o fluxo completo
4. Ajustar cores/estilos conforme necessário
