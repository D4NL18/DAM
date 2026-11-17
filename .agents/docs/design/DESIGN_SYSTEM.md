# Design System Mestre — Ecossistema DAM 🎨✨

Este documento define os tokens visuais, paleta semântica, regras tipográficas e os 8 estados interativos padronizados para o Frontend Angular 17 do DAM.

---

## 1. Paleta de Cores e Tokens Semânticos (`CSS Custom Properties`)

```scss
:root {
  /* Marca e Destaque */
  --color-primary: #2563eb;          /* Azul Primário Vibrante */
  --color-primary-hover: #1d4ed8;
  --color-secondary: #059669;        /* Verde Esmeralda (Sucesso / Positivo) */
  --color-secondary-hover: #047857;

  /* Superfícies e Fundos */
  --color-background: #f8fafc;       /* Slate 50 (Fundo Geral) */
  --color-surface: #ffffff;          /* Branco Puro para Cards */
  --color-surface-hover: #f1f5f9;    /* Slate 100 */

  /* Tipografia e Legibilidade */
  --color-on-background: #0f172a;    /* Slate 900 (Texto Principal) */
  --color-on-surface: #1e293b;       /* Slate 800 */
  --color-muted: #64748b;            /* Slate 500 (Texto Secundário) */

  /* Estados e Feedback */
  --color-error: #ef4444;            /* Red 500 (Erro / Débito) */
  --color-error-bg: #fef2f2;         /* Red 50 */
  --color-warning: #f59e0b;          /* Amber 500 */
  --color-warning-bg: #fffbeb;       /* Amber 50 */
  --color-success: #10b981;          /* Emerald 500 */
  --color-success-bg: #ecfdf5;       /* Emerald 50 */

  /* Bordas e Divisões */
  --border-color: #e2e8f0;           /* Slate 200 */
  --border-radius-sm: 6px;
  --border-radius-md: 10px;
  --border-radius-lg: 16px;
  --border-radius-full: 9999px;
}
```

---

## 2. Tipografia & Escala Modular (8pt Grid)

- **Fonte Principal:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`
- **Ícones:** `'Material Symbols Outlined'`
- **Hierarquia:**
  - `Display / H1:` 2.25rem (36px) | Peso: 700 | Tracking: `-0.02em`
  - `H2 (Títulos de Seção):` 1.5rem (24px) | Peso: 600
  - `H3 (Títulos de Card / Bento):` 1.125rem (18px) | Peso: 600
  - `Body / Texto Padrão:` 0.9375rem (15px) | Peso: 400 | Line-height: 1.5
  - `Caption / Muted:` 0.8125rem (13px) | Peso: 500

---

## 3. Os 8 Estados Interativos Obrigatórios

Cada componente interativo (botões, inputs, cards acionáveis) deve contemplar:
1. **Default:** Estado de repouso natural, contraste semântico nítido.
2. **Hover:** Elevação sutil (`translateY(-2px)`) e transição suave de cor (`150ms ease`).
3. **Active / Pressed:** Contração tátil (`scale(0.98)`).
4. **Focus-Visible:** Outline de acessibilidade de 2px (`outline: 2px solid var(--color-primary); outline-offset: 2px;`), sem anel em cliques de mouse.
5. **Loading / Skeleton:** Shimmer animado linear sem layout shift e bloqueio de cliques repetidos.
6. **Disabled:** Opacidade reduzida para 50%, cursor `not-allowed`, sem eventos de ponteiro.
7. **Empty State:** Ilustração ou ícone minimalista, texto explicativo claro e botão de ação primária (Call-to-Action).
8. **Error State:** Borda suave vermelha, mensagem explicativa amigável e botão "Tentar novamente" (sem engolir exceções).

---

## 4. Acessibilidade (A11y & WCAG 2.1 AA)

- **Contraste Mínimo de Cores:** Mínimo de 4.5:1 para texto normal e 3:1 para texto grande/ícones de status.
- **Navegação por Teclado:** Toda ação acessível via Tab e Enter/Espaço.
- **Anotações Semânticas:** Atributos `aria-label` em botões apenas com ícone.
