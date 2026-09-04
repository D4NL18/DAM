# Coleção: `user_addresses`

## 📋 Propósito

Armazena **endereços e locais favoritos** do usuário com apelidos semânticos. Permite consultar rotas usando apelidos como "casa", "trabalho", "academia" em vez de endereços completos. Os apelidos são normalizados e armazenados com coordenadas geográficas para uso no Google Maps.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **US-08 – Gerenciador de Endereços** | Utilitários | `salvar_endereco()`, `consultar_enderecos_salvos()` e `remover_endereco()` via `address_tool.py` |
| **US-05 – Mobilidade Urbana** | Utilitários | `maps_tool.py` usa `AddressRepository` para substituir apelidos por endereços reais |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/user_addresses/{safe_jid}__{safe_alias}`

Document ID: JID + alias normalizados com underscores (ex: `"5511999999999_s_whatsapp_net__casa"`).

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `user_jid` | `String` | Sim | JID do usuário no WhatsApp |
| `alias` | `String` | Sim | Apelido normalizado (sem acentos, minúsculas) |
| `address` | `String` | Sim | Endereço em texto bruto fornecido pelo usuário |
| `formatted_address` | `String` | Sim | Endereço formatado pelo Google Maps Geocoding API |
| `latitude` | `Number (Float)` | Opcional | Latitude obtida via geocoding |
| `longitude` | `Number (Float)` | Opcional | Longitude obtida via geocoding |
| `details` | `String` | Opcional | Informações adicionais (ex: `"Apto 42, Bloco B"`) |
| `updated_at` | `String (ISO 8601)` | Sim | Data/hora da última atualização |

---

## 🔗 Relacionamentos

Coleção autônoma. Coordenadas usadas diretamente na Google Maps Directions API.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Normalização de apelidos** | `normalize_alias()` remove acentos, lowercase e mapeia sinônimos: `"home"` → `"casa"`, `"firma"` → `"trabalho"` |
| **Isolamento por usuário** | Document ID = `user_jid + alias` garante isolamento entre usuários |
| **Cache L1 thread-safe** | `AddressRepository` usa `threading.RLock()` para proteger cache em memória |
| **Upsert por apelido** | `.set()` sobrescreve endereço existente para o mesmo apelido |

---

## 🗂️ Índices Necessários

| Campo | Ordem |
|---|---|
| `user_jid` | Ascendente |

---

## 🔒 Regras de Segurança

```
match /user_addresses/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Arquitetura de cache em duas camadas: **L1 em memória** (dict Python com RLock) e **L2 no Firestore**.
- Geocoding feito no cadastro — coordenadas persistidas para evitar chamadas repetidas à API.
