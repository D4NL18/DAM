# 🗺️ Funcionalidade: Mobilidade Urbana e Trânsito (Google Maps)

## 1. Descrição Geral
Permite estimar tempo de deslocamento em tempo real considerando tráfego intenso, acidentes e melhores rotas entre a localização atual e destinos frequentes (casa, trabalho, compromissos agendados), integrando à Google Maps Directions & Distance Matrix API.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Perguntando no WhatsApp
* *"Quanto tempo até o trabalho agora?"*
* *"Como está o trânsito até a Av Paulista?"*
* *"Que horas preciso sair para chegar às 14h no dentista considerando o trânsito?"*
* *"Qual a melhor rota para o aeroporto de Guarulhos hoje?"*

O bot responde com o tempo estimado de trajeto e o estado do tráfego:
```text
🚗 Estimativa de Rota (Google Maps):
• Destino: Av. Paulista, 1000
• Tempo estimado: 38 minutos (com trânsito moderado na Marginal)
• Distância: 18.4 km
• Rota recomendada: Via Av. 23 de Maio
```

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Calcular tempo de trajeto considerando tráfego em tempo real (live traffic).
* Sugerir o horário ideal de saída com base nos compromissos do Google Calendar.
* Comparar trajetos alternativos caso uma via principal esteja engarrafada.
* Suportar múltiplos modais de transporte (carro, transporte público ou a pé).

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Navegação GPS Turn-by-Turn em Tempo Real:** O DAM não substitui o Waze/Google Maps como navegador passo a passo na tela do carro durante a viagem.
* **Prever Blitz ou Radares Móveis:** O foco é na duração do percurso e vias congestionadas, não em fiscalizações policiais.
* **Garantir Horários em Situações Imprevistas:** Acidentes graves que ocorram após a consulta podem alterar o tempo real de chegada.
