# Regra de Negócio: Métodos de Pagamento Financeiros (RN-FIN-01)
 
## 1. Definição do Domínio
Toda despesa financeira registrada pelo DAM deve ser vinculada exclusivamente a uma das 3 modalidades de pagamento:
 
1. **`Cartão de Crédito Secundário`**: Cartão de crédito secundário/familiar do usuário.
2. **`Cartão de Crédito Pessoal`**: Cartão de crédito titular do usuário.
3. **`Cartão de Débito`**: Conta corrente e débito do usuário.
 
## 2. Regra de Transbordo para Pix
* **RN-FIN-01.1:** Pagamentos informados pelo usuário como **Pix** (ou transferência direta) são automaticamente catalogados como **`Cartão de Débito`**, refletindo a saída imediata de saldo da conta corrente.
 
## 3. Regra de Desambiguação / Omissão
* **RN-FIN-01.2:** Se o usuário relatar uma despesa sem declarar o método de pagamento (e o pagamento não for Pix), o motor de IA está **proibido** de inferir ou arbitrar um cartão.
* A IA deve obrigatoriamente realizar uma pergunta de esclarecimento:
  > *"Em qual dos seus cartões foi cobrado? No seu cartão de crédito pessoal, no secundário ou no débito?"*
* A gravação no banco de dados somente é autorizada após a confirmação do método pelo usuário.
