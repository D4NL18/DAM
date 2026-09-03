# 🍽️ Funcionalidade: Tradutor Gastronômico de Cardápios ao Vivo

## 1. Descrição Geral
Projetado para viagens internacionais e restaurantes com culinária exótica. O usuário fotografa o cardápio em qualquer idioma e o DAM não apenas traduz os nomes literais dos pratos, mas explica do que se trata cada receita, quais são os ingredientes típicos, nível de pimenta e alertas de alergênicos comuns.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Enviando a Foto no WhatsApp
1. Em um restaurante no exterior, aponte a câmera e tire uma foto nítida do cardápio (em francês, italiano, alemão, japonês, etc.).
2. Envie no chat do DAM com uma mensagem opcional:
   * *(Apenas a foto)* ou *"O que são estes pratos principais? Não gosto de frutos do mar."*
3. O bot responde em português explicando cada prato:
```text
🍽️ Cardápio Traduzido & Explicado:

1. 'Boeuf Bourguignon':
   • Tradução: Ensopado de carne bovina à Borgonha.
   • O que é: Carne cozida lentamente no vinho tinto com cenouras, cebolas e cogumelos. Prato quente, encorpado e macio.

2. 'Escargots de Bourgogne':
   • Tradução: Caracóis de terra com manteiga de alho e salsa.
   • Atenção: Aperitivo tradicional francês servido na concha.

3. 'Ratatouille':
   • Opção vegetariana clássica de legumes grelhados (berinjela, abobrinha, pimentão e tomate).
```

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Explicar o conceito gastronômico dos pratos além da tradução palavra por palavra.
* Filtrar pratos de acordo com restrições alimentares informadas na legenda (*"Sou intolerante a lactose"*, *"Não como porco"*).
* Identificar se o prato é apimentado, agridoce ou cru.
* Traduzir múltiplos idiomas (inglês, espanhol, francês, italiano, alemão, japonês, chinês, árabe, etc.).

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Garantir Isenção Total de Contaminação Cruzada:** Se o usuário tiver anafilaxia severa a algum alérgeno, o garçom e a cozinha devem ser avisados presencialmente.
* **Fazer o Pedido ao Garçom:** O bot apoia a compreensão do menu, mas não faz o pedido sonoro para a equipe do restaurante.
* **Ler Menus com Caligrafia Manual Muito Ilegível:** Textos em lousas de giz muito apagados ou com letra excessivamente cursiva podem ter perda de precisão.
