# Fase 11: Divisor Inteligente de Contas de Restaurante (Receipt OCR & Smart Split)

Este documento centraliza as especificações, regras de negócio e o planejamento de execução para a Fase 11, responsável pela divisão justa e automatizada de contas e comandas de restaurantes a partir de fotos de notas fiscais e comandos em linguagem natural.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1101 (OCR de Comandas e Notas Fiscais):** O usuário envia uma foto da conta do restaurante no WhatsApp. O bot, através do Gemini Vision, extrai estruturadamente todos os itens consumidos, quantidades e valores individuais, além do subtotal e da taxa de serviço (10% padrão ou percentual apontado na comanda).
- **P-1102 (Interpretação de Consumo em Linguagem Natural):** O usuário informa na mesma mensagem (ou logo em seguida por texto/áudio) quem consumiu o quê. Exemplos:
  - *"Eu comi o hambúrguer, o João bebeu as cervejas e a Maria dividiu a pizza comigo."*
  - *"Todos dividiram o couvert e a entrada; o Pedro pagou o vinho sozinho e cada um pagou seu prato principal."*
- **P-1103 (Rateio Justo e Proporcional):**
  - Itens consumidos individualmente são atribuídos 100% à pessoa indicada.
  - Itens compartilhados têm seus valores divididos igualmente entre os participantes envolvidos.
  - A taxa de serviço (10%) ou gorjeta é calculada proporcionalmente ao valor que cada pessoa consumiu (ou rateada igualmente caso solicitado).
- **P-1104 (Fechamento e Cobrança via Pix):**
  - O bot retorna um resumo elegante no WhatsApp discriminando o consumo de cada um e o total final por pessoa.
  - Inclui automaticamente a chave Pix cadastrada do usuário (`PIX_KEY`) com instruções claras para facilitar a transferência imediata pelos amigos.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 11

#### [ ] Task 11.1: OCR e Extração Estruturada com Gemini Vision
- [ ] **Etapa 11.1.1:** Criar módulo `backend_ia/services/bill_splitter_service.py`.
- [ ] **Etapa 11.1.2:** Implementar prompt especializado no Gemini Vision para converter imagens de notas fiscais em JSON estruturado com campos:
  - `items`: lista de `{ name: str, quantity: int, unit_price: float, total_price: float }`
  - `subtotal`: float
  - `service_tax_percent`: float (ex: 10.0)
  - `service_tax_value`: float
  - `discounts`: float
  - `total`: float

#### [ ] Task 11.2: Motor de Rateio e Mapeamento de Participantes
- [ ] **Etapa 11.2.1:** Implementar analisador semântico de atribuição (associar cada item do JSON extraído aos participantes citados no texto/áudio).
- [ ] **Etapa 11.2.2:** Desenvolver algoritmo matemático de divisão:
  - Calcular subtotal de consumo por pessoa.
  - Ratear itens compartilhados (ex: pizza / 2).
  - Aplicar taxa de serviço proporcional (`subtotal_pessoa * (service_tax_percent / 100)`).
  - Validar se a soma dos valores individuais bate exatamente com o total da conta (checagem de centavos).

#### [ ] Task 11.3: Tool LLM e Formatação de Resposta WhatsApp
- [ ] **Etapa 11.3.1:** Criar tool `backend_ia/services/tools/restaurant_split_tool.py` integrando o serviço de rateio.
- [ ] **Etapa 11.3.2:** Configurar variável de ambiente `USER_PIX_KEY` (chave Pix, nome do titular e banco).
- [ ] **Etapa 11.3.3:** Gerar template formatado para envio no WhatsApp:
  ```text
  🧾 *Divisão da Conta - Restaurante X*
  ---------------------------------
  🍔 *Você:* R$ 68,20
     - 1x Hambúrguer Artesanal (R$ 42,00)
     - 1/2 Pizza Margherita (R$ 20,00)
     - 10% de serviço: R$ 6,20

  🍺 *João:* R$ 39,60
     - 3x Cerveja IPA (R$ 36,00)
     - 10% de serviço: R$ 3,60

  🍕 *Maria:* R$ 22,00
     - 1/2 Pizza Margherita (R$ 20,00)
     - 10% de serviço: R$ 2,00
  ---------------------------------
  💰 *Total da Conta:* R$ 129,80
  
  📲 *Chave Pix para pagamento:*
  Chave: seu-email@exemplo.com (Nome do Titular)
  ```

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Leitura Precisa de Nota):** Foto de cupom fiscal com iluminação razoável é convertida em lista de itens e valores sem perda de centavos.
- [ ] **Cenário 2 (Divisão Mista e Compartilhada):** Comando com divisão de itens compartilhados e itens individuais calcula a fração exata para cada amigo.
- [ ] **Cenário 3 (Aplicação dos 10%):** A taxa de serviço é calculada e adicionada na proporção correta para cada pessoa, garantindo que quem consumiu menos pague menos taxa.
- [ ] **Cenário 4 (Consistência Matemática):** A soma exata cobrada de cada pessoa (com centavos) é igual ao total pago na comanda do restaurante.
- [ ] **Cenário 5 (Chave Pix Pronta):** A mensagem final inclui o valor exato e a chave Pix configurada para cópia rápida.
