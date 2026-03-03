# 📱 Configuração PWA - Ouvidoria Mogi

## ✅ Implementação Concluída

O Progressive Web App (PWA) foi configurado com sucesso!

### 📦 Dependências Instaladas

- `vite-plugin-pwa`: Plugin para gerar Service Worker e Manifest automaticamente
- `workbox-window`: Biblioteca para gerenciar atualizações do Service Worker

### ⚙️ Configurações Aplicadas

1. **Service Worker**: Gerado automaticamente com estratégia `generateSW`
2. **Auto-Update**: Habilitado (`registerType: 'autoUpdate'`)
3. **Manifest**: Configurado com nome, ícones e cores institucionais
4. **Offline Support**: Cache de assets e API com estratégias inteligentes
5. **Install Prompt**: Componente Vue para sugerir instalação

---

## 🎨 Gerar Ícones PWA

Os ícones são **obrigatórios** para o PWA funcionar. Você precisa criar:

### Opção 1: Gerar Online (Recomendado)

1. Acesse: https://realfavicongenerator.net/ ou https://www.pwabuilder.com/imageGenerator
2. Faça upload de uma imagem quadrada (mínimo 512x512px)
3. Baixe os ícones gerados
4. Coloque em `frontend/public/`:
   - `pwa-192x192.png` (192x192 pixels)
   - `pwa-512x512.png` (512x512 pixels)

### Opção 2: Criar Manualmente

Use um editor de imagens (GIMP, Photoshop, Figma) para criar:

- **192x192px**: Ícone pequeno (tela inicial mobile)
- **512x512px**: Ícone grande (splash screen)

**Recomendações:**
- Fundo transparente ou sólido (azul institucional #1e40af)
- Logo/texto centralizado
- Formato PNG
- Alta qualidade

### Opção 3: Placeholder Temporário

Por enquanto, os arquivos `pwa-192x192.png` e `pwa-512x512.png` estão como placeholders.
**Substitua-os antes de fazer deploy em produção!**

---

## 🚀 Como Testar

### 1. Instalar Dependências

```bash
cd frontend
npm install
```

### 2. Build do PWA

```bash
npm run build
```

O Vite gerará automaticamente:
- `dist/sw.js` (Service Worker)
- `dist/manifest.webmanifest` (Manifest JSON)
- Assets otimizados e cacheados

### 3. Testar Localmente

```bash
# Servir build de produção
npm run preview

# Ou usar servidor HTTP simples
npx serve dist
```

### 4. Testar Instalação

1. Abra `http://localhost:4173` (ou porta do preview)
2. Abra DevTools → Application → Service Workers
3. Verifique se o Service Worker está registrado
4. No Chrome/Edge: procure o ícone de instalação na barra de endereços
5. No mobile: aparecerá o prompt "Adicionar à tela inicial"

---

## 📱 Funcionalidades PWA

### ✅ Instalação
- Prompt automático quando o navegador detectar que o app é instalável
- Componente `InstallPrompt.vue` mostra banner discreto
- Usuário pode instalar ou adiar (lembra por 7 dias)

### ✅ Offline
- App funciona offline (serve arquivos cacheados)
- API usa estratégia `NetworkFirst` (tenta rede, depois cache)
- Imagens cacheadas por 30 dias

### ✅ Atualização Automática
- Quando você publicar nova versão, o app atualiza automaticamente
- Usuário não precisa fazer nada

### ✅ Experiência Nativa
- Remove barra de endereços (`display: standalone`)
- Tema azul institucional
- Ícones na tela inicial

---

## 🔧 Configurações Avançadas

### Alterar Cores

Edite `vite.config.ts`:

```typescript
manifest: {
  theme_color: '#1e40af', // Cor da barra de status
  background_color: '#ffffff', // Cor de fundo do splash screen
}
```

### Modificar Estratégia de Cache

Edite `workbox` em `vite.config.ts`:

```typescript
workbox: {
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/api\./,
      handler: 'NetworkFirst', // ou 'CacheFirst', 'StaleWhileRevalidate'
      // ...
    }
  ]
}
```

### Desabilitar PWA em Desenvolvimento

Em `vite.config.ts`, altere:

```typescript
devOptions: {
  enabled: false, // Desabilita PWA em dev
}
```

---

## 📋 Checklist de Deploy

Antes de fazer deploy em produção:

- [ ] Substituir ícones placeholder por ícones reais
- [ ] Testar instalação em Chrome/Edge
- [ ] Testar instalação em Android (Chrome)
- [ ] Testar instalação em iOS (Safari)
- [ ] Verificar funcionamento offline
- [ ] Testar atualização automática
- [ ] Verificar manifest.json no DevTools
- [ ] Validar Service Worker no DevTools

---

## 🐛 Troubleshooting

### Service Worker não registra

- Verifique se está servindo via HTTPS (ou localhost)
- Limpe cache do navegador
- Verifique console do DevTools

### Ícones não aparecem

- Verifique se os arquivos estão em `public/`
- Verifique se os caminhos no manifest estão corretos
- Limpe cache do navegador

### Prompt de instalação não aparece

- Verifique se está em HTTPS (ou localhost)
- Verifique se o manifest está válido
- Verifique se tem ícones configurados
- Verifique se `display: standalone` está configurado

---

## 📚 Recursos

- [Vite PWA Plugin Docs](https://vite-pwa-org.netlify.app/)
- [Web.dev PWA Guide](https://web.dev/progressive-web-apps/)
- [MDN Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)

---

**Última atualização**: 2026-02-17
