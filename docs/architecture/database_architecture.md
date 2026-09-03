# Arquitetura de Dados & Modelagem Firestore

## 1. Visão Geral
O DAM utiliza o **Google Cloud Firestore** (modo Nativo) como seu banco de dados principal serverless. O modelo documental NoSQL foi desenhado para garantir escalabilidade horizontal automática, custo zero em repouso (Always Free tier do GCP) e suporte a consultas atômicas indexadas.

Cada funcionalidade do sistema possui sua respectiva coleção dedicada, isolando contextos de dados e simplificando políticas de governança e retenção.

---

## 2. Catálogo de Coleções & Esquemas

### 2.1. `finances` (Gestão Financeira & Lançamentos)
Armazena compras, despesas fixas e variáveis com classificação de cartões.
```json
{
  "description": "Supermercado Pão de Açúcar",
  "amount": 184.50,
  "category": "Alimentação",
  "metodo_pagamento": "Cartão de Crédito Pessoal",
  "date": "2026-09-03",
  "created_at": "2026-09-03T14:30:00Z"
}
```
* **Índices Compostos:** `date DESC`, `category ASC, date DESC`.

### 2.2. `health_logs` / `health_metrics` (Saúde & Bem-Estar)
Métricas biométricas capturadas pelo assistente ou recebidas via Webhook do Apple Health / Health Auto Export.
```json
{
  "tipo": "sono",
  "horas": 7.5,
  "qualidade": "boa",
  "timestamp": "2026-09-03T07:00:00Z",
  "payload": { ... }
}
```

### 2.3. `notes_reminders` (Notas Rápidas & Lembretes)
Central de anotações e compromissos com flags de pendência.
```json
{
  "tipo": "lembrete",
  "titulo": "Comprar ração do gato",
  "conteudo": "Pacote de 10kg sabor salmão",
  "data_hora_lembrete": "2026-09-04T10:00:00",
  "status": "pendente",
  "tags": ["casa", "compras"],
  "created_at": "2026-09-03T12:00:00Z"
}
```

### 2.4. `vehicle_expenses` (Gestão Veicular)
Controle de custos por km e consumo de combustível.
```json
{
  "tipo": "abastecimento",
  "valor_total": 240.00,
  "litros": 41.5,
  "combustivel": "gasolina_aditivada",
  "odometro_km": 45200,
  "posto": "Posto Shell Piatã",
  "data": "2026-09-02"
}
```

### 2.5. `gift_ideas` (Curador de Presentes)
Ideias de presentes vinculadas a pessoas e ocasiões especiais.
```json
{
  "pessoa": "Camila",
  "relacao": "namorada",
  "ideia": "Kindle Paperwhite com capa de couro",
  "data_especial": "2026-11-20",
  "tags": ["livros", "tecnologia"],
  "created_at": "2026-09-01T18:00:00Z"
}
```

### 2.6. `item_locations` (Memória Espacial "Onde Guardei Isso?")
Rastreamento de localização física de objetos com histórico de movimentações.
```json
{
  "objeto": "Passaporte",
  "local_atual": "Gaveta trancada da escrivaninha do quarto",
  "categoria": "Documentos",
  "detalhes": "Junto com a pasta azul de certidões",
  "historico": [
    {
      "local": "Mochila de viagem",
      "data": "2026-07-15T10:00:00Z"
    }
  ],
  "updated_at": "2026-09-01T15:30:00Z"
}
```

### 2.7. `vault_credentials` (Cofre Criptografado de Senhas AES-256)
Armazenamento seguro com chaves e senhas criptografadas via algoritmo Fernet (AES-128-CBC com HMAC SHA-256) ou AES-256.
```json
{
  "servico": "GitHub",
  "usuario": "danielmarinho",
  "senha_criptografada": "gAAAAABl...",
  "notas": "Chave SSH principal vinculada",
  "updated_at": "2026-09-02T11:00:00Z"
}
```

### 2.8. `trip_groups` & `trip_expenses` (Splitwise de Viagens)
Gerenciamento de despesas compartilhadas em viagens com algoritmo determinístico de minimização de dívidas.
- **`trip_groups`:**
  ```json
  {
    "nome_viagem": "Morro de São Paulo",
    "participantes": ["Você", "Lucas", "Marina"],
    "created_at": "2026-08-20T10:00:00Z"
  }
  ```
- **`trip_expenses`:**
  ```json
  {
    "nome_viagem": "Morro de São Paulo",
    "descricao": "Passeio de Lancha",
    "valor": 450.00,
    "pagador": "Você",
    "participantes_divisao": ["Você", "Lucas", "Marina"],
    "data": "2026-08-21"
  }
  ```

### 2.9. `work_hours` (Banco de Horas Semanal)
Registro de jornadas de trabalho diárias e compensações de horas extras.
```json
{
  "data": "2026-09-03",
  "horas_trabalhadas": 8.5,
  "horas_trabalhadas_texto": "8h30",
  "meta_diaria_horas": 8.0,
  "saldo_dia_horas": 0.5,
  "descricao": "Deploy da nova versão da API"
}
```

### 2.10. `anime_watchlist` (Anime Tracker & AniList)
Rastreamento e espelhamento oficial de animes acompanhados.
```json
{
  "anilist_id": 164983,
  "titulo_principal": "Mushoku Tensei: Isekai Ittara Honki Dasu Season 3",
  "titulo_ingles": "Mushoku Tensei Season 3",
  "status_transmissao": "RELEASING",
  "total_episodios": 12,
  "status_usuario": "assistindo",
  "ultimo_episodio_visto": 10,
  "nota_usuario": 9.5,
  "proximo_episodio": {
    "episodio": 11,
    "airing_at": 1788500000,
    "data_formatada": "07/09/2026 às 11:30",
    "tempo_restante_segundos": 320000
  },
  "updated_at": "2026-09-03T16:00:00Z"
}
```

### 2.11. `briefing_logs` (Idempotência do Morning Briefing)
Garante envio único diário às 08:00 mesmo em caso de reinicialização de instâncias.
```json
{
  "data": "2026-09-03",
  "enviado": true,
  "enviado_as": "2026-09-03T08:00:05Z",
  "destinatario": "5571****9995@s.whatsapp.net"
}
```

### 2.12. `chats` (Histórico de Conversas & Contexto de IA)
Armazena os últimos diálogos trocados com o assistente no WhatsApp para alimentar a janela de contexto de 10 turnos do Gemini.
```json
{
  "remoteJid": "5571991269995@s.whatsapp.net",
  "fromMe": false,
  "text": "Quanto gastei com mercado este mês?",
  "message_id": "3EB0...",
  "timestamp": "2026-09-03T14:25:00Z"
}
```

---

## 3. Segurança e Políticas de Acesso
- Acesso exclusivo pelo SDK de Admin (`firebase-admin`) autenticado via chave de serviço ou identidade gerenciada do Cloud Run (Workload Identity).
- Regras de segurança padrão bloqueiam qualquer acesso direto client-side não autenticado.
