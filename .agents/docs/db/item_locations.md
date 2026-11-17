# Coleção: `item_locations`

## 📋 Propósito

Implementa a **Memória Espacial** do DAM — repositório de localização de objetos físicos e documentos do usuário. Cada documento representa um objeto rastreado com seu local atual e histórico cronológico de todas as localizações anteriores.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **GP-03 – Memória Espacial** | Gestão Pessoal | `registrar_localizacao_objeto()`, `onde_guardei_objeto()` e `listar_historico_movimentacoes()` em `item_finder_tool.py` |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/item_locations/{objeto_lower}`

Document ID é o nome do objeto em minúsculas (ex: `"passaporte"`). Garante busca exata O(1).

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `objeto` | `String` | Sim | Nome original com capitalização preservada |
| `objeto_lower` | `String` | Sim | Nome em minúsculas — usado como Document ID e para busca por palavras-chave |
| `local_atual` | `String` | Sim | Descrição textual do local atual |
| `categoria` | `String` | Sim | Categoria (ex: `"Documentos"`, `"Veículos"`, `"Acessórios"`, `"Geral"`) |
| `detalhes` | `String` | Opcional | Informações contextuais adicionais |
| `atualizado_em` | `String (ISO 8601)` | Sim | Data/hora da última atualização |
| `historico` | `Array<Map>` | Sim | Lista de localizações anteriores (pode ser vazia) |

### Sub-documento: `historico[]`

| Campo | Tipo | Descrição |
|---|---|---|
| `local` | `String` | Local anterior |
| `data` | `String (ISO 8601)` | Data/hora do registro neste local |
| `detalhes` | `String` | Detalhes adicionais (pode ser null) |

---

## 🔗 Relacionamentos

Coleção autônoma. Document ID como chave direta de busca.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Upsert com histórico** | Ao registrar novo local para objeto existente, o local anterior é adicionado ao `historico[]` |
| **Document ID = objeto_lower** | Chave do documento é o nome normalizado. Garante unicidade por objeto |
| **Busca por palavras-chave** | Quando busca exata falha, varredura linear comparando contra `objeto_lower`, `detalhes` e `categoria` |
| **Fallback em memória** | `_in_memory_items` como cache e fallback quando Firestore está indisponível |

---

## 🗂️ Índices Necessários

Não são necessários índices compostos.

---

## 🔒 Regras de Segurança

```
match /item_locations/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- O array `historico[]` é ilimitado. Considerar política de truncamento para objetos muito movimentados.
- Busca semântica simulada por correspondência de substring. Sem embeddings ou busca vetorial nesta versão.
