# 🔐 Funcionalidade: Cofre Seguro de Credenciais e Informações Sensíveis

## 1. Descrição Geral
Permite consultar informações sensíveis de rotina (senhas de Wi-Fi de convidados, números de contratos, códigos de portão eletrônico ou chaves de emergência) criptografadas ponta a ponta com **AES-256 GCM** e autenticação multifator via WhatsApp.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Armazenando um Segredo
* *"Guarde no cofre a senha do Wi-Fi da casa de praia: PraiaSol2026! com chave mestre"*
* *"Armazene o código do portão social: 9842"*

### Resgatando com Segurança
1. O usuário solicita no chat:
   * *"Qual a senha do Wi-Fi de hóspedes?"*
2. O bot solicita a confirmação do PIN ou senha de cofre:
   * *"Para revelar esta credencial, confirme seu PIN de segurança."*
3. O usuário digita o PIN correto e o bot revela a informação, excluindo a mensagem temporária logo após.

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Criptografia forte AES-256 no banco de dados Firestore.
* Exigir PIN ou senha de liberação para dados marcados como estritamente confidenciais.
* Resgatar rapidamente dados que o usuário precisa compartilhar com visitas sem precisar levantar para ler a etiqueta do roteador.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Substituir o 1Password/Bitwarden para Navegação Web:** Não faz preenchimento automático de senhas (autofill) no Google Chrome ou no navegador móvel.
* **Armazenar CVV de Cartões de Crédito:** Por diretrizes estritas de segurança e conformidade PCI-DSS, o bot recusa o armazenamento de códigos de segurança de cartões bancários.
* **Recuperar Segredos se a Chave Mestre For Esquecida:** Criptografia de conhecimento zero (zero-knowledge) impede descriptografia se o usuário perder o segredo principal.
