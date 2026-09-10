# Contrato de Integração de API: Evolution API Media Download

## 1. Visão Geral
Este contrato define a interface de comunicação HTTP síncrona entre o `backend_ia` do DAM e a Evolution API para extração sob demanda de mídias criptografadas (imagens, áudios e documentos) recebidas via WhatsApp.

---

## 2. Endpoints

### 2.1. `POST /chat/getBase64FromMediaMessage/{instance}`
**Objetivo:** Obter a representação em Base64 e metadados de uma mídia recebida via WhatsApp.

**Requisição (Request):**
- **Autenticação:** Header `apikey: {EVOLUTION_API_KEY}`
- **Headers:** `Content-Type: application/json`
- **Path Params:** `instance`: Nome da instância (ex.: `DAM_Instance`)
- **Payload/Body:**
```json
{
  "message": {
    "key": {
      "id": "3EB0ABC123456"
    }
  },
  "convertToMp4": false
}
```

**Resposta de Sucesso (200 OK):**
```json
{
  "base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
  "mimetype": "image/jpeg",
  "filename": "imagem.jpeg"
}
```
*(Nota: O campo `base64` pode vir com ou sem prefixo `data:<mime>;base64,` dependendo da versão interna da Evolution API).*

**Respostas de Erro Mapeadas:**
- **400 Bad Request:** Mensagem não encontrada no cache/banco da Evolution API.
- **401 Unauthorized:** API key ausente ou inválida.
- **500 / Timeout:** Falha de conexão ou timeout na comunicação com os servidores da Meta.

---

## 3. Implementação no Backend (`WhatsAppService`)
- **Método:** `WhatsAppService.get_base64_from_media_message(message_id: str, message_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]`
- **Timeout:** 15 segundos.
- **Retorno Padronizado:** Dicionário com `{"base64": str, "mimetype": str}` ou `None`.
- **Tratamento de Exceções:** Captura silenciosa de `requests.exceptions.RequestException`, log de aviso mascarado e fallback seguro.
