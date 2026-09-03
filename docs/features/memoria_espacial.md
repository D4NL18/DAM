# 🗝️ Funcionalidade: Memória Espacial ("Onde Guardei Isso?")

## 1. Descrição Geral
Resolve o problema de esquecer onde objetos pouco usados ou documentos importantes foram guardados em casa. O usuário manda uma mensagem rápida ao guardar algo e, meses depois, pode perguntar a localização exata do objeto.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Registrando onde guardou
* *"Guardei o passaporte na segunda gaveta do gaveteiro do escritório"*
* *"A chave reserva do Fastback está dentro da caixa azul em cima do armário do quarto"*
* *"Deixei as ferramentas na prateleira inferior da garagem"*

### Perguntando onde está
* *"Onde está o meu passaporte?"*
* *"Onde guardei a chave reserva do carro?"*
* *"Cadê a minha furadeira?"*

O bot responde imediatamente:
```text
🗝️ O seu passaporte está guardado na segunda gaveta do gaveteiro do escritório (registrado em 12/03/2026).
```

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Mapear cômodos, móveis, gavetas, caixas e prateleiras.
* Busca semântica por sinônimos (*"documentos de viagem"* $\rightarrow$ passaporte).
* Atualizar o local caso o usuário informe que mudou o objeto de lugar (*"Mudei o passaporte para o cofre"*).
* Informar a data em que o item foi registrado para dar segurança de quando foi guardado.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Rastreamento Físico por GPS ou Bluetooth:** O bot não usa tags físicas (como Apple AirTag) para triangulação geográfica de itens perdidos fora de casa.
* **Saber se Alguém Mexeu:** Se outra pessoa da casa mudar o objeto de lugar sem avisar o bot, a memória refletirá o último local informado pelo usuário.
