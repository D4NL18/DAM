# Fase 15: Calculadora Inteligente de Churrasco e Eventos

Este documento centraliza as especificações, regras de negócio e planejamento de execução para a Fase 15, responsável pelo dimensionamento exato de compras para churrascos e eventos.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1501 (Entradas Flexíveis em Linguagem Natural):** O usuário pode descrever o evento livremente por texto ou áudio (ex.: *"Vou fazer um churrasco para 12 adultos (8 bebem cerveja) e 4 crianças, das 14h às 20h"*). O bot deve extrair:
  - Número total de adultos.
  - Subgrupo de adultos que consomem cerveja e que não consomem álcool.
  - Número de crianças.
  - Horário de início e término (duração em horas, pois eventos mais longos consomem mais insumos).
- **P-1502 (Parâmetros Per Capita de Consumo):**
  - **Carnes:** Média padrão de 400g a 500g por adulto e 200g a 250g por criança para eventos de até 4h, escalando proporcionalmente para durações maiores (ex: 6h). Distribuição balanceada por tipo:
    - Carne Bovina nobre/grelha (ex: Picanha, Maminha, Fraldinha): ~50%
    - Linguiça toscana: ~20%
    - Frango (coxinha da asa/sobrecoxa): ~15%
    - Carne Suína/Costelinha: ~15%
  - **Carvão:** Média de 1kg a 1,5kg de carvão para cada 1kg a 1,2kg de carne.
  - **Cerveja:** Média de 1,5L a 2L (4 a 6 latas de 350ml) por bebedor para 4 horas; proporcionalmente mais para 6 horas (ex: 7 a 9 latas por pessoa).
  - **Bebidas Não Alcoólicas:** 600ml a 800ml por pessoa (refrigerante, água e suco).
  - **Gelo:** ~1 saco de 5kg para cada 3 a 4 pessoas (para resfriar bebidas e copos).
  - **Complementos:** Pão de alho (1 a 2 unidades por pessoa), queijo coalho e farofa.
- **P-1503 (Formatação da Lista de Compras):** A resposta deve ser gerada como um checklist limpo e organizado em tópicos para ser facilmente encaminhado ou aberto no supermercado/açougue.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 15

#### [ ] Task 15.1: Motor Matemático de Dimensionamento de Churrasco
- [ ] **Etapa 15.1.1:** Criar módulo `backend_ia/services/bbq_calculator_service.py` com funções puras de cálculo baseadas em coeficientes per capita e duração do evento.
- [ ] **Etapa 15.1.2:** Implementar arredondamentos práticos para compras reais (ex.: fardos de 12 latas, sacos fechados de carvão de 2,5kg ou 5kg, sacos de gelo de 5kg, embalagens de pão de alho).

#### [ ] Task 15.2: Tool LLM `bbq_planner_tool.py`
- [ ] **Etapa 15.2.1:** Criar `backend_ia/services/tools/bbq_planner_tool.py` com a função:
  - `calcular_churrasco(adultos_total: int, adultos_bebem_cerveja: int, criancas: int, duracao_horas: float, tipo_evento: str = 'churrasco_padrao')`
- [ ] **Etapa 15.2.2:** Registrar os schemas no `backend_ia/services/ai_service.py` para extração autônoma a partir de frases completas.
- [ ] **Etapa 15.2.3:** Template de resposta amigável no WhatsApp com visual destacado e estimativa de custo aproximado (opcional).

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Comando Completo):** Usuário envia "Churrasco para 12 adultos (8 bebem) e 4 crianças, das 14h às 20h (6h)". O cálculo considera as 6 horas de festa e fornece quantitativo de carnes separadas por tipo, carvão, fardos de cerveja, refrigerante e gelo.
- [ ] **Cenário 2 (Comando Sem Informar Duração):** Usuário diz "Churrasco para 10 adultos". O sistema assume uma duração padrão de 4 horas ou pergunta gentilmente se o evento será muito longo.
- [ ] **Cenário 3 (Formatação da Lista):** A resposta chega formatada com emojis e bullets para facilitar o envio no WhatsApp e leitura no mercado.
