# Fase 13: Cofre Seguro de Senhas e Credenciais (Criptografia AES-256 & SecOps)

Este documento centraliza as especificações, regras de negócio e planejamento técnico da Fase 13, dedicada ao armazenamento seguro de senhas, credenciais e acessos protegidos.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1301 (Segurança de Nível Bancário - Zero-Knowledge):** Nenhuma senha ou segredo pode ser salvo em texto puro no Firestore. O valor da senha deve ser cifrado utilizando AES-256-GCM antes de sair da memória do serviço.
- **P-1302 (Sanitização Absoluta de Logs):** É estritamente proibido gravar senhas, tokens ou textos planos de credenciais nos logs da aplicação (`chat_logs`, stdout/console ou arquivos de log). Qualquer tentativa de registro deve substituir a senha por `[REDACTED_SECRET]`.
- **P-1303 (Estrutura de Registro de Credencial):** Cada credencial deve armazenar:
  - `service`: Nome do serviço/site (ex: "Netflix", "Wi-Fi Casa", "Conta Gov.br").
  - `username`: Usuário/e-mail/login.
  - `password_encrypted`: Texto cifrado com AES-256-GCM.
  - `iv` e `tag`: Vetor de inicialização e tag de integridade para a decifragem autenticada.
  - `notes_encrypted`: Anotações ou perguntas de segurança complementares (opcionais, também cifradas).
  - `updated_at`: Data da última alteração.
- **P-1304 (Recuperação e Exibição de Senhas):** Ao solicitar uma senha (ex.: *"Qual é a senha do Wi-Fi de casa?"*, *"Qual a senha da Netflix?"*), o bot descriptografa em memória e envia uma resposta objetiva. Pode incluir a opção de gerar nova senha forte e sugerir rotação periódica.

---

## 2. Planejamento das Tarefas (Arquitetura & SecOps)

### Tarefas da Fase 13

#### [ ] Task 13.1: Módulo Criptográfico e Chaves de Segurança
- [ ] **Etapa 13.1.1:** Implementar serviço utilitário `backend_ia/services/security/crypto_service.py` utilizando `cryptography` (AES-GCM).
- [ ] **Etapa 13.1.2:** Configurar derivação ou injeção da chave mestra segura (`VAULT_MASTER_KEY` via GCP Secret Manager ou variável de ambiente protegida).
- [ ] **Etapa 13.1.3:** Implementar sanitização no `ChatRepository.save_log` para mascarar padrões de senha antes de salvar em `chat_logs`.

#### [ ] Task 13.2: Modelagem da Coleção Segura `vault_credentials` no Firestore
- [ ] **Etapa 13.2.1:** Criar `backend_ia/repositories/vault_repository.py`.
- [ ] **Etapa 13.2.2:** Métodos para inserir/atualizar credenciais cifradas e buscar por serviço e remote_jid.

#### [ ] Task 13.3: Tool LLM `password_vault_tool.py`
- [ ] **Etapa 13.3.1:** Criar funções da tool:
  - `salvar_senha(servico: str, usuario: str, senha: str, anotacoes: Optional[str] = None)`
  - `consultar_senha(servico: str)`
  - `gerar_senha_forte(tamanho: int = 16, incluir_simbolos: bool = True)`
  - `listar_servicos_cadastrados()` (retorna apenas a lista dos nomes dos serviços e logins, sem as senhas).
- [ ] **Etapa 13.3.2:** Registrar schemas no `services/ai_service.py` para detecção de intenções de credenciais.

---

## 3. Critérios de Aceite e Validação (QA & SecOps)
- [ ] **Cenário 1 (Persistência Segura):** Ao salvar a senha da "Netflix", inspecionar o documento no Firestore e validar que o campo `password` não existe em texto puro, contendo apenas payload hexadecimal/base64 cifrado (`iv`, `tag`, `ciphertext`).
- [ ] **Cenário 2 (Sanitização de Logs):** A mensagem contendo a senha digitada pelo usuário não deve ter a senha visível no histórico de `chat_logs`.
- [ ] **Cenário 3 (Consulta de Senha):** O usuário pergunta "Qual a senha do Wi-Fi de casa?". O sistema localiza o serviço, decifra a senha em memória e envia no chat privado com o usuário.
- [ ] **Cenário 4 (Gerador de Senha):** O usuário pede "Crie uma senha forte de 16 caracteres para o serviço X". O bot gera a senha com entropia adequada e oferece salvá-la no cofre.
