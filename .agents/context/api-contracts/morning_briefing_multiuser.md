# Contrato de Integração e Arquitetura: Morning Briefing Multi-Usuário (GP-04.1)

## 1. Visão Geral
Este documento define as especificações de API e arquitetura interna para o disparo e consulta do Morning Briefing individualizado, filtros de animes e alertas de Clash of Clans.

---

## 2. Endpoints RESTful

### `POST /api/briefing/morning`
Dispara o Morning Briefing para os usuários ativos no WhatsApp.

- **Headers:**
  - `apikey: string` ou `Authorization: Bearer <token>` (Obrigatório)
- **Query Parameters:**
  - `force: boolean` (Opcional, default: `false`) — Força o reenvio mesmo que já tenha sido disparado hoje.
  - `user_id: string` (Opcional, default: `None`) — Se informado (`daniel` ou `lari`), dispara unicamente para aquele usuário. Se omitido, dispara para todos os usuários que tiverem o briefing ativo.
- **Responses:**
  - `200 OK`:
    ```json
    {
      "status": "ok",
      "mensagem": "Briefing matinal processado para todos os usuários ativos.",
      "detalhes": [
        {"userId": "daniel", "status": "sucesso", "destinatario": "5571991269995"},
        {"userId": "lari", "status": "sucesso", "destinatario": "5571983278254"}
      ]
    }
    ```
  - `401 Unauthorized`: Token inválido ou ausente.

### `GET /api/briefing/preview`
Pré-visualização do texto do briefing de um usuário sem disparar pelo WhatsApp.
- **Headers:** `apikey` ou `Authorization`
- **Query Parameters:**
  - `user_id: string` (Opcional, default: `None` -> usuário ativo ou `daniel`)
- **Responses:**
  - `200 OK`: `{"status": "ok", "userId": "lari", "preview": "..."}`

---

## 3. Contratos de Ferramentas Internas (Python)

### `notes_tool.py`
- `listar_lembretes_pendentes(apenas_hoje: bool = False, data_referencia: Optional[str] = None) -> str`
  - Se `apenas_hoje=True` ou `data_referencia` informada: filtra apenas itens onde a data em `data_hora_lembrete` bate com a data informada (`YYYY-MM-DD`).
  - Higieniza a exibição de `tags` sem duplicação de colchetes ou aspas.

### `anime_tracker_tool.py`
- `_obter_info_animes_briefing(data_hoje: Optional[datetime] = None) -> str`
  - Filtro estrito: `status_usuario == 'assistindo'`.
- `listar_meus_animes(status: Optional[str] = None) -> str`
  - Se `status == 'planejo_assistir'` ou se for consulta de animes para assistir: retorna itens `planejo_assistir` e itens `assistindo` com `ultimo_episodio_visto == 0`.
- `consultar_novas_temporadas(titulo_anime: str)` e `explorar_temporada_animes(estacao, ano)`:
  - Respeitam a regra P-0413 (apenas animes em `assistindo` ou `concluido`).

### `clash_of_clans_tool.py`
- `_verificar_raid_season(data: dict, player_tag: str) -> str | None`
  - Se `state == "ongoing"` e `membro is None`: retorna alerta informando 5 ataques disponíveis para realizar.
- `_obter_alertas_coc() -> str` em `briefing_service.py`
  - Concatena independentemente alertas de Raid Weekend e de Guerra/CWL.

### `briefing_service.py`
- `enviar_briefing_matinal(force: bool = False, user_id: Optional[str] = None) -> str`
  - Usa contexto isolado para o usuário alvo.
- `enviar_briefings_agendados(hora_atual: str, force: bool = False) -> List[Dict[str, Any]]`
  - Avalia todos os usuários cadastrados e envia se `horario == hora_atual`.
