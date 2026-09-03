# Fase 12: Memória Espacial e Localizador de Objetos ("Onde Guardei Isso?")

Este documento centraliza as especificações, regras de negócio e o planejamento de execução para a Fase 12, dedicada à memória contextual e espacial de objetos e itens guardados.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1201 (Captura Espontânea de Localização):** O usuário pode enviar frases informais em texto ou áudio sempre que guardar algo importante (ex.: *"Guardei o passaporte na gaveta de cima do armário do quarto"*, *"A chave reserva do carro está dentro da caixa preta da sala"*). O bot deve extrair:
  - `item`: Objeto ou documento guardado (ex.: "passaporte", "chave reserva do carro").
  - `location`: Descrição clara e contextual do local onde foi guardado.
  - `category`: Categoria inferida (Documentos, Chaves, Eletrônicos, Roupas, Ferramentas, etc.).
  - `details`: Detalhes complementares fornecidos (ex.: "gaveta de cima", "caixa preta").
- **P-1202 (Busca Semântica e Resposta Amigável):** Quando o usuário perguntar pelo item (ex.: *"Onde guardei meu passaporte?"*, *"Cadê a chave reserva?"*, *"O que tem guardado na caixa preta?"*), o assistente deve buscar semanticamente no banco e responder de forma direta e amigável.
- **P-1203 (Atualização de Localização e Histórico):** Se o usuário disser *"Mudei o passaporte para a pasta azul na estante"*, o registro ativo do item deve ser atualizado para o novo local, arquivando o anterior como histórico para evitar confusões.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 12

#### [ ] Task 12.1: Modelagem da Coleção `item_locations` no Firestore
- [ ] **Etapa 12.1.1:** Criar `backend_ia/repositories/items_repository.py` manipulando a coleção `item_locations`.
- [ ] **Etapa 12.1.2:** Estrutura dos documentos:
  - `id`: ID único do item.
  - `remote_jid`: Identificador do usuário.
  - `item_name`: Nome padronizado do item (ex: "passaporte brasileiro").
  - `location`: Descrição do local atual.
  - `category`: Categoria do objeto.
  - `tags`: Palavras-chave para busca rápida.
  - `previous_locations`: Lista de locais antigos com timestamp.
  - `updated_at`: Timestamp da última modificação.

#### [ ] Task 12.2: Tool LLM `item_finder_tool.py`
- [ ] **Etapa 12.2.1:** Criar as funções principais da tool:
  - `salvar_local_item(item: str, localizacao: str, categoria: Optional[str] = None)`
  - `buscar_local_item(termo_busca: str)`
  - `listar_itens_por_local(local: str)`
- [ ] **Etapa 12.2.2:** Registrar os schemas no `services/ai_service.py` para detecção autônoma via Gemini Function Calling.

#### [ ] Task 12.3: Refinamento Semântico e Sinônimos
- [ ] **Etapa 12.3.1:** Garantir tolerância a variações ("passaporte", "meu passaporte", "documento de viagem").
- [ ] **Etapa 12.3.2:** Prompts de confirmação concisos (ex: *"Anotado! O passaporte está na gaveta de cima do armário do quarto."*).

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Registro via Texto):** Usuário digita "A chave reserva do carro está na caixa preta". O bot confirma que registrou o local da chave reserva.
- [ ] **Cenário 2 (Consulta com Variação de Termos):** Usuário pergunta "Cadê a chave do carro?". O bot responde que a chave reserva está na caixa preta.
- [ ] **Cenário 3 (Atualização de Local):** Usuário diz "Coloquei o passaporte dentro da mochila preta". O bot atualiza o local e confirma.
- [ ] **Cenário 4 (Consulta Inversa por Local):** Usuário pergunta "O que eu guardei na caixa preta?". O bot lista que a chave reserva do carro está armazenada lá.
