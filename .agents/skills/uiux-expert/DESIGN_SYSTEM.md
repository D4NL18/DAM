# Design System Base (Dashboard DAM)

## Visão Geral
Este documento rege as escolhas estéticas e arquiteturais de UI/UX do Frontend (Angular). O objetivo é criar uma interface limpa, focada em dados, que não transpareça ter sido "gerada por IA" (vide `UI_ANTI_PATTERNS.md` se aplicável).

## 1. Tipografia
- **Família de Fonte Principal:** `Inter` (Google Fonts).
- **Escala Base:** `16px = 1rem`
- **Pesos:**
  - `400 (Regular)`: Corpo de texto.
  - `500 (Medium)`: Botões e labels de gráficos.
  - `700 (Bold)`: Títulos principais (H1, H2).

## 2. Paleta de Cores
- **Fundo Principal (Background):** `#F8FAFC` (Slate 50) - Fugir do branco puro para conforto visual.
- **Superfícies (Cards):** `#FFFFFF`
- **Textos Escuros:** `#0F172A` (Slate 900)
- **Textos Mutados (Legendas):** `#64748B` (Slate 500)
- **Cor Primária (Ações principais):** `#0EA5E9` (Sky 500) - Um tom moderno, sereno, não o azul clichê.
- **Cor de Destaque / Alerta (Financeiro/Veículo):** `#F59E0B` (Amber 500) e `#10B981` (Emerald 500).

## 3. Espaçamentos e Grid
- Uso obrigatório de **múltiplos de 8px** (0.5rem) em todos os paddings e margins.
- **Respiro:** Seções distintas do dashboard devem ter no mínimo `48px` (3rem) ou `64px` (4rem) de espaçamento.

## 4. Sombras e Bordas
- **Cards e Painéis:** 
  - `border-radius: 12px;`
  - `box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);` (Sombra muito difusa e fraca).
- **Elementos Flutuantes/Modais:** Sombra ligeiramente mais forte, mas translúcida.

## 5. Estados Vazios e Carregamentos
- Telas de Dashboard que ainda não carregaram devem exibir um **Skeleton Loader** suavemente animado.
- Gráficos sem dados devem exibir um ícone ilustrativo acompanhado de texto encorajador. Nenhum "Spinner" perdido no centro da tela é aceitável.
