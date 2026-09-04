# Tarefa: GP-01.1 – CRUD Completo: Edição In-Place e Exclusão Segura no Google Calendar

## 📋 Contexto
Identificado que o assistente DAM possuía apenas gendar_evento e consultar_agenda. Ao solicitar a exclusão de uma reunião, o bot confirmava a remoção sem executar ação na API do Google Calendar. Ao solicitar a alteração/remarcação de uma reunião, chamava gendar_evento criando um evento duplicado.

---

## 🎯 Checklist de Implementação (Arquiteto)

- [x] **1. TDD / Testes Unitários (	ests/test_calendar_crud.py):**
  - [x] Teste de exclusão bem-sucedida (excluir_evento) com verificação da chamada events().delete().
  - [x] Teste de exclusão com evento inexistente (retorno amigável sem erro 500).
  - [x] Teste de exclusão com múltiplos eventos ambíguos (retorno de lista para desambiguação).
  - [x] Teste de edição bem-sucedida (editar_evento) com events().patch() alterando horário.
  - [x] Teste de edição bem-sucedida alterando título, descrição e localização.
  - [x] Teste de matriz de permissões: Lari bloqueada de excluir ou editar evento na agenda de Daniel.
  - [x] Teste de Daniel com permissão para gerenciar agenda própria e agenda da Lari (usuario="lari").

- [x] **2. Implementação das Tools (services/tools/calendar_tool.py):**
  - [x] Função auxiliar _localizar_eventos_por_termo(service, calendar_id, termo, data_referencia) para busca inteligente de eventos.
  - [x] Função excluir_evento(termo_busca, data_referencia, usuario="auto").
  - [x] Função editar_evento(termo_busca, novo_titulo, novo_inicio_iso, nova_duracao_minutos, nova_descricao, nova_localizacao, data_referencia, usuario="auto").
  - [x] Aprimoramento de consultar_agenda para estruturar e contextualizar melhor os eventos.

- [x] **3. Integração com o Motor de IA (services/ai_service.py):**
  - [x] Importação de editar_evento e excluir_evento.
  - [x] Registro em AVAILABLE_TOOLS para o Gemini.

- [x] **4. Prompting & Regras de Sistema:**
  - [x] Validação de instruções comportamentais para direcionar a IA a usar editar_evento ao invés de gendar_evento quando o usuário pedir para remarcar/mudar/alterar.
  - [x] Validação de instruções comportamentais para direcionar excluir_evento quando pedir para cancelar/remover/excluir.

- [x] **5. Validação & QA:**
  - [x] Execução dos testes novos e suíte completa de 325 testes sem regressões.
