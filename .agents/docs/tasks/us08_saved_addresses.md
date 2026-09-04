# Checklist da Tarefa: US-08 Gerenciador de Endereços & Locais Salvos

- **ID da Tarefa:** `TASK-US08-001`
- **Domínio:** 5. Utilitários & Segurança
- **Status:** Concluído (100%)

---

## Checklist de Implementação

### 1. Suíte de Testes TDD (Tester)
- [x] Criar `backend_ia/tests/test_saved_addresses.py`:
  - [x] Teste de normalização de apelidos ("minha casa" -> "casa", "meu trabalho" -> "trabalho", "academia").
  - [x] Teste de salvamento e recuperação em `AddressRepository` com mock do Firestore.
  - [x] Teste de isolamento multi-tenant por `user_jid`.
  - [x] Teste de remoção de endereço.
  - [x] Teste das tools `salvar_endereco`, `consultar_enderecos_salvos` e `remover_endereco`.
  - [x] Teste de integração com `maps_tool.resolver_apelido_endereco` priorizando o endereço salvo no Firestore.
  - [x] Teste de fallback para `settings.py` quando o endereço não está no Firestore.
  - [x] Teste de cálculo de rota ("casa" para "trabalho") usando os endereços dinâmicos do banco.

### 2. Implementação do Repositório e Tools (Dev)
- [x] Criar `backend_ia/repositories/address_repository.py`:
  - [x] Singleton com cache L1 thread-safe (`threading.RLock`).
  - [x] Métodos `save_address`, `get_address`, `list_addresses`, `delete_address`.
  - [x] Normalizador de apelidos `normalize_alias`.
- [x] Criar `backend_ia/services/tools/address_tool.py`:
  - [x] `salvar_endereco(apelido: str, endereco: str, detalhes: str = "")`: Consulta Geocoding API se disponível, salva e retorna confirmação formatada.
  - [x] `consultar_enderecos_salvos(apelido: str = "")`: Lista todos os endereços ou detalha um específico.
  - [x] `remover_endereco(apelido: str)`: Remove e confirma.
- [x] Atualizar `backend_ia/services/tools/maps_tool.py`:
  - [x] Injetar consulta ao `AddressRepository` em `resolver_apelido_endereco`.
- [x] Registrar novas tools em `backend_ia/services/ai_service.py`.

### 3. Validação e Qualidade (Reviewer, UX, QA, SecOps, DevOps)
- [x] Code Review (Clean Code, tipagem, PEP 8, zero vazamento de memória).
- [x] UX Reviewer (preservação de mensagens legíveis e amigáveis no WhatsApp).
- [x] Execução completa do pytest (11/11 testes aprovados).
- [x] SecOps (auditoria de isolamento multi-tenant).
- [x] DevOps (atualização de estado e baseline).

