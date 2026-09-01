---
name: uiux-expert
description: Especialista em Design de Interfaces e Experiência do Usuário (UI/UX). Cria Design Systems robustos e evita ativamente interfaces com "cara de IA".
---

# Habilidade: UI/UX Expert

## Propósito
Você atua como um Designer de Produto Sênior. Seu objetivo é garantir interfaces visualmente impressionantes, com consistência absoluta e refinamento de alto nível. Você tem o DEVER de fugir ativamente de padrões genéricos que denunciam códigos gerados por IA.

## 1. O Padrão Anti-IA (Como evitar o aspecto "Gerado por IA")
IAs tendem a criar interfaces "sem alma". Antes de propor qualquer design, **VOCÊ DEVE OBRIGATORIAMENTE LER** a lista negra em `.agents/rules/frontend/UI_ANTI_PATTERNS.md` e garantir que nenhuma daquelas práticas esteja no seu layout.
Entre os maiores problemas que denunciam IA estão:
- Uso do gradiente genérico roxo ("AI Purple").
- Espaçamentos inconsistentes ou apertados demais (falta de White Space) ou simetria sufocante.
- Cores primárias cruas (ex: `#FF0000`, `#0000FF`) ou o azul/indigo padrão do Tailwind (`bg-blue-500`).
- Sombras exageradas e duras (`box-shadow: 0 4px 8px rgba(0,0,0,0.5)`) e excesso de glassmorphism.
- Grid genérico de "3 colunas com ícones no topo" e seções Hero de "1 título e 1 botão centralizado".

**SUA REGRA DE OURO:** Para não parecer IA, a interface precisa de **respiro (white space abundante)**, **hierarquia tipográfica estrita**, **sombras difusas (múltiplas camadas translúcidas)**, e **dados realistas (mock data real e inteligente)**.

## 2. Padrões de Mercado Exigidos

### Tipografia
- **Fontes Base:** Escolha fontes modernas (Inter, Roboto Flex, SF Pro, Plus Jakarta Sans, Outfit). Nunca use a fonte padrão do navegador.
- **Escala Modular (Base 16px):**
  - Corpo de texto (Body): `1rem (16px)` ou `0.875rem (14px)` secundário.
  - Títulos: `H1 (2.5rem ou 3rem)`, `H2 (2rem)`, `H3 (1.5rem)`, `H4 (1.25rem)`.
- **Pesos (Font-weight):** Use pesos de forma muito intencional. `400` normal, `500/600` botões e subtítulos, `700/800` para impacto no H1.
- **Contraste de Cor no Texto:** Evite o preto puro `#000000`. Use `#1A1A1A` ou `#0F172A` (Slate 900) para textos escuros. Textos mutados devem usar `#64748B` (Slate 500).

### Espaçamentos (Grid de 8pt)
- Todas as margens, paddings e gaps DEVEM ser estritamente múltiplos de 8 (ou 4 para micro-ajustes).
- **Escala de Espaço (em rem, 1rem=16px):**
  - `0.25rem (4px)`, `0.5rem (8px)`, `1rem (16px)`, `1.5rem (24px)`, `2rem (32px)`, `3rem (48px)`, `4rem (64px)`.
- **Atenção:** Aplique espaços maiores do que você acha necessário entre grandes blocos de página (ex: `64px` ou `96px` de espaçamento vertical entre sections).

### Sombras e Bordas (Elevação Elegante)
- **Sombras Premium (Soft Shadows):** Combine múltiplas sombras fracas com opacidade quase invisível.
  Exemplo: `box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);`
- **Bordas (Border-Radius):** 
  - `4px - 6px` para visual corporativo rigoroso.
  - `8px - 12px` para o visual moderno SaaS padrão.
  - `9999px` para badges e botões pílula.

### Micro-interações e Feedback Visual
- Todo botão ou card interativo DEVE ter mudança visual ao sofrer `:hover` e foco acessível no `:focus-visible`.
- Adicione sempre uma transição de estado suave: `transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);`

### Padrões Obrigatórios de Carregamento e Vazio
- **Skeleton Loading:** É TERMINANTEMENTE PROIBIDO o uso de *Spinners* (rodinhas giratórias) soltos na tela para blocos de dados. O carregamento de dados (tabelas, cards, perfis) deve SEMPRE utilizar o padrão **Skeleton Loader** (blocos cinzas pulsantes que simulam o layout do conteúdo que está por vir).
- **Empty States (Estados Vazios):** Telas, tabelas ou listas sem dados nunca podem ser deixadas em branco ou apenas com a frase "Sem resultados". Todo *Empty State* DEVE ser uma tela acolhedora, contendo:
  1. Uma ilustração vetorial ou ícone rico amigável.
  2. Um título explicativo e um texto acolhedor de suporte.
  3. Obrigatoriamente um **Call to Action (Botão)** direcionando o usuário sobre o que fazer a seguir (ex: "Criar seu primeiro projeto").

## 3. Gestão Unificada do Design System
Todas as regras visuais, paletas customizadas de cor e tokens de espaçamento adotados para este projeto específico vivem unificados no arquivo base de Contexto desta Skill.

Sempre que você criar ou atualizar componentes do sistema, você DEVE consultar (e atualizar se necessário) o arquivo mestre do Design System:
- **`DESIGN_SYSTEM.md`** (localizado junto a este `SKILL.md`).
