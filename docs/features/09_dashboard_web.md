# 📊 Funcionalidade: Dashboard Web (Bento Grid & Métricas)

## 1. Descrição Geral
Interface web moderna desenvolvida em **Angular 17 (Standalone Components & SCSS Puro)** que apresenta as métricas consolidadas de Saúde, Finanças, Veículo e Rotinas em um layout no formato Bento Grid, com estética glassmorphism e tema dark mode.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Acessando Localmente
1. No diretório `frontend_dashboard`, execute:
   ```bash
   npm start
   ```
2. Abra seu navegador em `http://localhost:4200/`.

### Navegação pelos Módulos
* **Visão Geral (Home):** Resumo dos principais indicadores (passos do dia, gastos do mês, status do veículo).
* **Painel de Saúde (`/health`):** Gráficos de passos diários, frequência cardíaca e distribuição de calorias.
* **Painel Financeiro (`/finances`):** Gráfico de pizza por categoria, histórico das últimas transações e balanço de despesas.
* **Menu Lateral:** Alternância rápida entre seções com indicadores de status em tempo real.

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Exibir dashboards reativos consumindo dados da Core API Spring Boot / Firestore.
* Proporcionar experiência visual premium com paleta Tailwind/Cyberpunk (fundo escuro, cards translúcidos, tipografia Inter).
* Gráficos dinâmicos renderizados com ApexCharts ou Chart.js.
* Responsividade total para desktops, tablets e smartphones.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Edição de Código em Tempo Real:** O painel é uma SPA voltada para visualização e acompanhamento de métricas, não uma IDE ou terminal.
* **Acesso Público sem Rede Autorizada:** Em produção, o painel fica restrito ao ambiente do usuário configurado no Firebase Hosting.
* **Operação sem Conexão de Dados:** Requer conexão de rede para consultar a Core API e carregar as séries temporais.
