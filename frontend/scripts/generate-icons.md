# 🎨 Gerar Ícones PWA

## Método Rápido (Online)

### Opção 1: RealFaviconGenerator
1. Acesse: https://realfavicongenerator.net/
2. Faça upload de uma imagem quadrada (mínimo 512x512px)
3. Configure:
   - **Android Chrome**: Marque "Android Chrome"
   - **Windows Metro**: Opcional
4. Baixe o pacote
5. Extraia `android-chrome-192x192.png` e `android-chrome-512x512.png`
6. Renomeie e coloque em `frontend/public/`:
   - `pwa-192x192.png`
   - `pwa-512x512.png`

### Opção 2: PWA Builder Image Generator
1. Acesse: https://www.pwabuilder.com/imageGenerator
2. Faça upload de uma imagem
3. Baixe os ícones gerados
4. Coloque em `frontend/public/`

## Método Manual (Figma/GIMP/Photoshop)

1. Crie um canvas quadrado:
   - **192x192px** para o ícone pequeno
   - **512x512.png** para o ícone grande

2. Design:
   - Fundo: Azul institucional (#1e40af) ou transparente
   - Logo/texto: Branco ou contraste adequado
   - Centralize o conteúdo
   - Deixe margem de segurança (~10% de cada lado)

3. Exporte como PNG:
   - Alta qualidade (100%)
   - Sem compressão excessiva

4. Coloque em `frontend/public/`:
   - `pwa-192x192.png`
   - `pwa-512x512.png`

## Placeholder Temporário (Desenvolvimento)

Se você só quer testar o PWA sem criar ícones agora:

1. Use qualquer imagem quadrada temporária
2. Ou use um gerador de placeholder:
   - https://via.placeholder.com/192x192/1e40af/ffffff?text=O
   - https://via.placeholder.com/512x512/1e40af/ffffff?text=O

**⚠️ IMPORTANTE**: Substitua os placeholders antes do deploy em produção!
