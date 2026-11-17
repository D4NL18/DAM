# Coleção: `gift_ideas`

## 📋 Propósito

Armazena **ideias de presentes** capturadas durante conversas naturais com o DAM. Cada documento vincula uma ideia a uma pessoa e, opcionalmente, a uma data comemorativa. Funciona como curador proativo com alertas de aproximação de datas.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **EL-06 – Curador de Ideias de Presentes** | Entretenimento | `salvar_ideia_presente()`, `consultar_ideias_presente()` e `alertar_datas_proximas()` |
| **GP-04 – Morning Briefing** | Gestão Pessoal | `alertar_datas_proximas()` incluido no briefing para datas especiais próximas |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/gift_ideas/{auto_id}`

Document ID gerado automaticamente via `.add()`.

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String (UUID)` | Sim | UUID v4 gerado pelo backend |
| `pessoa` | `String` | Sim | Nome da pessoa a ser presenteada (ex: `"Mariana"`, `"Mãe"`) |
| `relacao` | `String` | Sim | Grau de relação (ex: `"namorada"`, `"mãe"`, `"amigo"`) |
| `ideia` | `String` | Sim | Descrição da ideia de presente (ex: `"Kindle Paperwhite"`) |
| `data_especial` | `String` | Opcional | Data comemorativa em formato livre (ex: `"15/05"`, `"2026-10-12"`) |
| `tags` | `Array<String>` | Opcional | Tags/categorias (ex: `["tecnologia", "leitura"]`) |
| `data_captura` | `String (ISO 8601)` | Sim | Data/hora de registro da ideia (UTC) |
| `created_at` | `Timestamp` | Sim | Timestamp Firestore nativo da criação |

---

## 🔗 Relacionamentos

Coleção autônoma. Relacionamento lógico por `pessoa` e `relacao`.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Parsing de datas flexível** | Suporta ISO, brasileiro (DD/MM/YYYY) e recorrente (DD/MM) |
| **Alerta antecipado** | `alertar_datas_proximas(dias_antecedencia=30)` filtra próximos 30 dias |
| **Projeção de datas recorrentes** | Datas `DD/MM` já passadas há mais de 30 dias são projetadas para o ano seguinte |
| **Filtro case-insensitive** | Filtros por `pessoa` e `relacao` usam substring em lowercase |

---

## 🗂️ Índices Necessários

| Campo | Ordem |
|---|---|
| `pessoa` | Ascendente |

---

## 🔒 Regras de Segurança

```
match /gift_ideas/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Múltiplas ideias por pessoa — sem restrição de unicidade.
- Fallback em memória `_MOCK_GIFT_IDEAS` para testes unitários.
- `_parse_special_date()` usa regex para extrair datas válidas da string livre.
