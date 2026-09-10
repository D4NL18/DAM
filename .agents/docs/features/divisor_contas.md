# 🧾 Funcionalidade: Divisor de Contas de Restaurante (OCR de Comanda)

## 1. Descrição Geral
Permite fotografar a conta do restaurante ao final de uma refeição em grupo. O DAM realiza OCR nos itens, calcula taxa de serviço (10% a 15%) e rateia os valores exatos de acordo com o consumo individual de cada pessoa (quem bebeu álcool vs quem não bebeu).

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Enviando a Foto no WhatsApp
1. Tire uma foto nítida da comanda ou conta do restaurante.
2. Envie no chat com a instrução de divisão:
   * *"Foto da conta: éramos 4 pessoas, mas só o Lucas e eu tomamos cerveja. O prato principal foi dividido por todos. Calcule quanto cada um paga com 10% de serviço"*
3. O DAM retorna o extrato detalhado:
```text
🧾 Fechamento da Conta:
• Total da comanda: R$ 320,00
• Taxa de serviço (10%): R$ 32,00
• Total geral: R$ 352,00

Divisão por pessoa:
- Lucas: R$ 102,00 (Prato + Cervejas + 10%)
- Você: R$ 102,00 (Prato + Cervejas + 10%)
- Ana: R$ 74,00 (Prato + Sucos + 10%)
- Carlos: R$ 74,00 (Prato + Sucos + 10%)
```

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Ler recibos impressos, comandas fiscais e notas de maquininhas de cartão.
* Separar itens de consumo compartilhado de itens de consumo exclusivo.
* Aplicar taxas de serviço ou gorjetas configuráveis.
* Gerar resumo pronto para copiar e colar no grupo de amigos do WhatsApp.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Cobrança Automática por Pix:** Não cobra os amigos pelo aplicativo do banco (apenas indica a chave Pix do pagador para transferência manual).
* **Contas com Rasuras Excessivas:** Se o recibo estiver rasgado, manchado de gordura ou com valores cortados na borda da foto, o cálculo pode exigir correção manual.
