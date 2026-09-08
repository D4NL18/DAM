# Coleção: `briefing_preferences`
**Domínio:** Gestão Pessoal & Rotina (Morning Briefing Multi-Usuário)
**ID Épico:** GP-04.1

## 📋 Propósito
Armazena as configurações e preferências personalizadas de cada usuário para o Morning Briefing (mensagem de bom dia), incluindo horário de envio, tópicos selecionados e flag de ativação.

---

## 📑 Estrutura do Documento
**Path no Firestore:** `/briefing_preferences/{userId}`
Document ID determinístico: `userId` (ex: `"daniel"`, `"lari"`).

### Campos
| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `userId` | `String` | Sim | Identificador único do usuário (`daniel` ou `lari`) |
| `userName` | `String` | Sim | Nome de exibição (`Daniel`, `Lari`) |
| `horario` | `String` | Sim | Horário de envio no fuso de Brasília (formato `HH:MM`, ex: `"07:30"`, `"08:00"`) |
| `topicos` | `Array<String>` | Sim | Lista de tópicos ativos (`agenda`, `lembretes`, `saude`, `furia`, `animes`, `clash`, `veiculo`) |
| `ativo` | `Boolean` | Sim | Indica se o envio diário automático está ativado |

---

## 🔒 Regras de Segurança e Performance
- Sem perda de dados: atualizações utilizam `set(..., merge=True)` ou preservam defaults.
- Acesso sempre por Document ID direto $O(1)$.
