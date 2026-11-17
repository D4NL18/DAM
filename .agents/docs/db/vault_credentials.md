# Coleção: `vault_credentials`

## 📋 Propósito

Armazena **credenciais criptografadas** do usuário. Implementa um cofre de senhas **Zero-Knowledge** com criptografia simétrica autenticada (Fernet/AES-128 CBC + HMAC-SHA256). A senha **nunca** é armazenada em texto plano.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **US-01 – Cofre Criptografado de Senhas** | Utilitários & Segurança | `salvar_credencial()`, `consultar_credencial()` e `listar_servicos_cofre()` em `password_vault_tool.py` |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/vault_credentials/{servico_lower}`

Document ID é o nome do serviço em minúsculas (ex: `"github"`, `"netflix"`).

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `servico` | `String` | Sim | Nome original do serviço (ex: `"GitHub"`) |
| `servico_lower` | `String` | Sim | Nome em minúsculas — Document ID e busca por substring |
| `usuario` | `String` | Sim | Nome de usuário ou e-mail (texto plano) |
| `senha_criptografada` | `String` | Sim | Ciphertext Fernet da senha |
| `notas` | `String` | Opcional | Informações adicionais (ex: `"2FA habilitado"`) |
| `atualizado_em` | `String (ISO 8601)` | Sim | Data/hora da última atualização |

---

## 🔗 Relacionamentos

Coleção autônoma.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Criptografia obrigatória** | Se a criptografia falhar, a operação é abortada com erro |
| **Upsert por serviço** | `.set()` sobrescreve a credencial existente. Um documento por serviço |
| **Máscara por padrão** | Consulta retorna senha mascarada (`Abc****z9`). `revelar_senha=True` exige explícito |
| **Chave derivada via PBKDF2** | 100.000 iterações SHA-256 com salt fixo `dam_vault_secure_salt_pbkdf2_2026` |

---

## 🗂️ Índices Necessários

Nenhum — busca exata por Document ID.

---

## 🔒 Regras de Segurança

```
match /vault_credentials/{docId} {
  allow read, write: if false;
}
```

---

## 🛡️ SecOps

- **`usuario` em texto plano:** Email/username não é criptografado por design.
- **Salt fixo:** `dam_vault_secure_salt_pbkdf2_2026` é estático. Menos robusto que salt por credencial.
- **Fernet é AES-128-CBC + HMAC-SHA256** — não AES-256 como nomeado na feature.

---

## 📌 Observações Técnicas

- Fallback em memória `_in_memory_vault` para testes unitários.
- Logs de operações sanitizados — conteúdo da senha nunca aparece nos logs.
