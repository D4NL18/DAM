# 💰 Funcionalidade: Gestão Financeira & Lançamento de Gastos

## 1. Descrição Geral
Permite o registro rápido de despesas e receitas no dia a dia diretamente pelo WhatsApp. A IA extrai valores, categorias, descrições e formas de pagamento, gravando as transações na coleção `finances` do Firestore.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Três Carteiras Pré-definidas
As saídas são classificadas rigorosamente entre 3 contas/cartões cadastrados:
1. **Cartão de Crédito Secundário (Compartilhado):** Cartão de crédito secundário ou familiar.
2. **Cartão de Crédito Pessoal:** Cartão de crédito titular do usuário.
3. **Cartão de Débito / Pix:** Conta corrente e débito (qualquer transação via **Pix** é automaticamente classificada aqui).

---

## 2. Como Utilizar no Dia a Dia

### Exemplos de Registro de Gastos

#### Exemplo 1: Informando o cartão diretamente
* *"Almocei por 45 reais no débito"* $\rightarrow$ Registra R$ 45,00 em **Cartão de Débito**.
* *"Gastei 150 reais no mercado no crédito pessoal"* $\rightarrow$ Registra R$ 150,00 em **Cartão de Crédito Pessoal**.
* *"Paguei 80 reais de farmácia no cartão secundário"* $\rightarrow$ Registra R$ 80,00 em **Cartão de Crédito Secundário**.
* *"Fiz um Pix de 35 reais para o estacionamento"* $\rightarrow$ Registra automaticamente em **Cartão de Débito**.

#### Exemplo 2: Omissão do cartão (A IA pergunta obrigatoriamente)
* **Você:** *"Almocei por 48 reais"*
* **DAM:** *"Em qual dos seus cartões foi cobrado? No cartão de crédito pessoal, no secundário ou no débito?"*
* **Você:** *"No secundário"*
* **DAM:** *"Perfeito! Registrei o gasto de R$ 48,00 com 'Almoço' no **Cartão de Crédito Secundário**."*

### Consultando o Saldo e Relatórios
* *"Quanto gastei no cartão de crédito secundário este mês?"*
* *"Qual foi meu total no cartão de crédito pessoal?"*
* *"Como estão minhas despesas no débito/Pix?"*

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Distinguir e registrar o método de pagamento exato em cada transação no banco de dados (`Cartão de Crédito Secundário`, `Cartão de Crédito Pessoal`, `Cartão de Débito`).
* Converter automaticamente pagamentos informados como **Pix** para a carteira de **Débito**.
* Bloquear o registro e perguntar de forma natural e educada caso você esqueça de informar a forma de pagamento.
* Extrair automaticamente valor, categoria, data e descrição.
* Gravar transações instantaneamente para análise posterior no Dashboard.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Registrar sem Método Definido:** O bot recusa registrar uma despesa sem que uma das 3 modalidades seja selecionada.
* **Movimentar Dinheiro Real:** O bot não realiza transferências bancárias, não faz pagamentos Pix e não acessa seu saldo bancário diretamente.
* **Cancelar Compras:** O DAM apenas registra os livros contábeis pessoais, sem vínculo operacional com as operadoras de cartão.
* **Leitura Automática de Extrato Bancário:** Requer que o usuário informe o gasto no chat ou envie a foto do comprovante.
