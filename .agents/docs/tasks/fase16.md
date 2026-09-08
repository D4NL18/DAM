# Fase 16: Tradutor e Guia Gastronômico de Cardápios ao Vivo (Vision OCR & Contexto Cultural)

Este documento centraliza as especificações, regras de negócio e planejamento de execução para a Fase 16, responsável por auxiliar em viagens internacionais fotografando cardápios e recebendo explicações contextuais de pratos.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1601 (Leitura Visual de Cardápios):** O usuário envia uma foto do cardápio físico tirada com o celular em um restaurante no exterior. O Gemini Vision deve realizar o OCR multilíngue em qualquer idioma (ex: Francês, Italiano, Alemão, Japonês, Grego, Espanhol, Russo).
- **P-1602 (Tradução Cultural e Gastronômica):**
  - O bot não deve apenas fazer traduções literais robóticas. Ele deve explicar a essência de cada prato relevante (ex.: *"É um tipo de ensopado tradicional de carne cozida lentamente com batatas e legumes no vinho tinto"* ou *"Massa fresca recheada com queijo de ovelha típico da região"*).
  - Destacar o tipo de proteína principal (carne bovina, frango, porco, peixe, frutos do mar ou vegetariano).
- **P-1603 (Destaque e Recomendações):** Se o cardápio for muito longo, o bot pode agrupar por seções (Entradas, Pratos Principais, Sobremesas) e destacar os pratos mais clássicos ou populares.
- **P-1604 (Alertas Alimentares):** Capacidade de avisar sobre pratos com frutos do mar, pimenta intensa, glúten ou nozes/amendoim.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 16

#### [ ] Task 16.1: Pipeline de Imagem no Gemini Vision
- [ ] **Etapa 16.1.1:** Criar serviço especializado `backend_ia/services/menu_translator_service.py`.
- [ ] **Etapa 16.1.2:** Estruturar prompt com papel de Sommelier / Guia Gastronômico de Viagem, instruindo o modelo a formatar cada prato com:
  - *Nome Original* (Tradução em Português)
  - *Explicação*: ingredientes, estilo de cozimento e sabor/textura.
  - *Destaques*: prato clássico, picante, vegetariano, etc.

#### [ ] Task 16.2: Tool LLM `menu_translator_tool.py`
- [ ] **Etapa 16.2.1:** Integrar a recepção da imagem vinda do webhook do WhatsApp (`imageMessage`).
- [ ] **Etapa 16.2.2:** Detecção automática de intenção quando o usuário envia foto de cardápio (acompanhada ou não de mensagens como *"O que é bom aqui?"* ou *"Me explica esse cardápio"*).

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Cardápio em Francês):** Usuário envia foto com "Boeuf Bourguignon". O bot traduz e explica: *"Prato clássico francês: ensopado de carne bovina marinada e cozida lentamente em vinho tinto da Borgonha, servido com cebolas, cogumelos e batatas"*.
- [ ] **Cenário 2 (Cardápio em Italiano):** Usuário envia foto com "Cacio e Pepe". O bot explica que é uma massa com molho à base de queijo pecorino e pimenta-do-reino moída na hora.
- [ ] **Cenário 3 (Foto Parcial ou Ruim):** Se o texto de alguma parte estiver ilegível pelo ângulo ou iluminação, o bot avisa quais itens conseguiu decifrar e pede outra foto mais próxima se necessário.
