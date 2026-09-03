# Fase 17: Conversor Universal Instantâneo (Medidas, Pesos e Temperaturas)

Este documento centraliza as especificações, regras de negócio e planejamento de execução para a Fase 17, dedicada a conversões universais instantâneas, determinísticas e precisas no WhatsApp sem necessidade de buscas manuais no Google.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1701 (Conversão Determinística e Livre de Alucinações):** O cálculo matemático de conversão deve ser executado por código Python determinístico, garantindo exatidão decimal estrita e evitando que o LLM "invente" fórmulas ou valores aproximados incorretos.
- **P-1702 (Escopo Completo de Unidades Suportadas):**
  - **Distância / Comprimento:**
    - Milhas (mi) <-> Quilômetros (km): `1 mi = 1.609344 km`
    - Pés (ft) <-> Centímetros (cm) / Metros (m): `1 ft = 30.48 cm` (ou `0.3048 m`)
    - Polegadas (in) <-> Centímetros (cm): `1 in = 2.54 cm`
    - Jardas (yd) <-> Metros (m): `1 yd = 0.9144 m`
  - **Temperatura:**
    - Fahrenheit (°F) <-> Celsius (°C): `°C = (°F - 32) * 5/9`
    - Contexto de forno/culinária (ex: 350°F no forno americano equivale a ~175°C no forno brasileiro, 180°F equivale a ~82°C).
  - **Massa / Peso:**
    - Libras (lb) <-> Quilogramas (kg): `1 lb = 0.45359237 kg`
    - Onças (oz) <-> Gramas (g): `1 oz = 28.3495231 g`
  - **Volume e Cozinha (Opcional):**
    - Galões americanos (gal) <-> Litros (L): `1 gal = 3.78541 L`
    - Onças fluidas (fl oz) <-> Mililitros (ml): `1 fl oz = 29.5735 ml`
- **P-1703 (Linguagem Natural Informal):** O usuário pode mandar mensagens rápidas do tipo:
  - *"Quantos KM dá 35 milhas?"*
  - *"180 Fahrenheit é quanto no forno daqui?"*
  - *"6 pés de altura dá quantos centímetros?"*
  - *"Quanto é 160 libras em kg?"*
- **P-1704 (Resposta Instantânea e Direta):** A resposta deve ser imediata e direta ao ponto, mostrando o resultado convertido com destaque e a fórmula/referência breve.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 17

#### [ ] Task 17.1: Motor Matemático de Conversão de Unidades
- [ ] **Etapa 17.1.1:** Criar `backend_ia/services/converter_service.py` com dicionário de fatores de conversão e funções com arredondamento configurável (ex: 2 casas decimais).
- [ ] **Etapa 17.1.2:** Suporte a conversões compostas (ex: 5 pés e 11 polegadas em metros/cm).

#### [ ] Task 17.2: Tool LLM `unit_converter_tool.py`
- [ ] **Etapa 17.2.1:** Criar `backend_ia/services/tools/unit_converter_tool.py` com funções:
  - `converter_distancia(valor: float, de_unidade: str, para_unidade: str)`
  - `converter_temperatura(valor: float, de_unidade: str, para_unidade: str)`
  - `converter_peso(valor: float, de_unidade: str, para_unidade: str)`
  - `converter_volume(valor: float, de_unidade: str, para_unidade: str)`
- [ ] **Etapa 17.2.2:** Registrar os schemas no `ai_service.py` para acionamento via Function Calling do Gemini.

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Milhas para KM):** "Quantos KM dá 35 milhas?" -> Retorna: `35 milhas = 56,33 km`.
- [ ] **Cenário 2 (Fahrenheit para Celsius):** "180 Fahrenheit é quanto no forno daqui?" -> Retorna: `180 °F = 82,2 °C`.
- [ ] **Cenário 3 (Pés para Centímetros):** "6 pés em cm?" -> Retorna: `6 pés (ft) = 182,88 cm (1,83 m)`.
- [ ] **Cenário 4 (Libras para KG):** "150 libras em kg?" -> Retorna: `150 lb = 68,04 kg`.
