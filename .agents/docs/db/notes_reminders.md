# Coleção: `notes_reminders`

## 📋 Propósito

Armazena **anotações pessoais** e **lembretes agendados** do usuário em uma única coleção polimórfica. Cada documento tem o tipo determinado pelo campo discriminador `tipo`. É o segundo cérebro digital do usuário — repositório de conhecimento pessoal e agenda de compromissos informais.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **GP-02 – Notas e Lembretes Rápidos** | Gestão Pessoal | Criação, busca e conclusão de anotações e lembretes via `notes_tool.py` |
| **GP-04 – Morning Briefing** | Gestão Pessoal | `briefing_service.py` chama `listar_lembretes_pendentes()` para incluir tarefas do dia |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/notes_reminders/{item_id}`

Document ID é o UUID v4 gerado pelo backend.

### Campos Comuns

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String (UUID)` | Sim | UUID v4 gerado pelo backend. Também usado como Document ID |
| `tipo` | `String (Enum)` | Sim | Discriminador: `"nota"` ou `"lembrete"` |
| `titulo` | `String` | Sim | Título conciso do item |
| `tags` | `Array<String>` | Opcional | Etiquetas em minúsculas para categorização |
| `created_at` | `String (ISO 8601)` | Sim | Data/hora de criação em UTC |
| `updated_at` | `String (ISO 8601)` | Sim | Data/hora da última atualização em UTC |

### Campos de Anotações (`tipo = "nota"`)

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `conteudo` | `String` | Sim | Corpo completo da anotação |

### Campos de Lembretes (`tipo = "lembrete"`)

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `data_hora_lembrete` | `String` | Sim | Data e hora em formato livre (ex: `"2026-09-04 15:00"`) |
| `status` | `String (Enum)` | Sim | Estado: `"pendente"` ou `"concluido"` |
| `concluido_em` | `String (ISO 8601)` | Opcional | Data/hora em que o lembrete foi concluído |

---

## 🔗 Relacionamentos

Coleção autônoma. Relacionamento lógico implícito com a agenda via `briefing_service.py`.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Tags normalizadas** | Tags sempre em minúsculas via `strip().lower()` |
| **Busca em memória** | Busca por `termo` feita por varredura — sem índice de texto no Firestore |
| **Conclusão irreversível** | Uma vez concluído, lembrete não retorna para `"pendente"` |
| **Coleção polimórfica** | Notas e Lembretes compartilham a mesma coleção; separação pelo campo `tipo` |

---

## 🗂️ Índices Necessários

| Campo | Ordem |
|---|---|
| `tipo` | Ascendente |
| `status` | Ascendente |

---

## 🔒 Regras de Segurança

```
match /notes_reminders/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Fallback em memória `_mock_storage` para testes unitários e quando Firestore está indisponível.
- O campo `data_hora_lembrete` é string livre — sem suporte a range queries por data de lembrete.
