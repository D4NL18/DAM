# Contrato de API & Function Calling: Conversor de Arquivos (US-09)

## 1. Visão Geral
Define as interfaces RESTful do FastAPI e as ferramentas de Function Calling (Gemini) para operações de conversão, junção, fatiamento e transcodificação de documentos e mídias.

---

## 2. Endpoints REST (FastAPI)

### 2.1. `POST /api/files/convert`
**Descrição:** Executa a conversão do arquivo enviado e retorna o binário convertido com cabeçalho `Content-Disposition` para download imediato.

- **Headers:**
  - `Authorization: Bearer <token>` ou chave de usuário
  - `X-User-Id: admin` (opcional, default extraído do token/contexto)
- **Form Data (Multipart):**
  - `file`: UploadFile (arquivo principal - binário)
  - `additional_files`: List[UploadFile] (opcional, usado em `merge_pdfs` ou `images_to_pdf`)
  - `conversion_type`: string (obrigatório: `pdf_to_docx`, `docx_to_pdf`, `img_to_pdf`, `merge_pdfs`, `split_pdf`, `pdf_to_images`, `image_convert`, `pdf_to_text`)
  - `options`: JSON string opcional (ex: `{"pages": "1-3", "target_format": "PNG", "quality": 90}`)
- **Respostas:**
  - `200 OK`: Stream binário do arquivo gerado (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `image/png`, `text/plain`).
  - `400 Bad Request`: Formato inválido, tamanho excedido (>25MB) ou documento corrompido.
  - `500 Internal Server Error`: Falha no processamento.

### 2.2. `GET /api/files/supported-formats`
**Descrição:** Lista todas as conversões suportadas, formatos de entrada e saída e limites.

- **Resposta `200 OK` (JSON):**
  ```json
  {
    "supported_conversions": [
      {"type": "img_to_pdf", "from": ["jpg", "jpeg", "png", "webp"], "to": "pdf"},
      {"type": "merge_pdfs", "from": ["pdf"], "to": "pdf"},
      {"type": "split_pdf", "from": ["pdf"], "to": "pdf"},
      {"type": "pdf_to_docx", "from": ["pdf"], "to": "docx"},
      {"type": "docx_to_pdf", "from": ["docx"], "to": "pdf"},
      {"type": "pdf_to_images", "from": ["pdf"], "to": ["png", "jpg"]},
      {"type": "image_convert", "from": ["png", "jpg", "jpeg", "webp", "bmp"], "to": ["png", "jpg", "webp"]},
      {"type": "pdf_to_text", "from": ["pdf"], "to": "txt"}
    ],
    "max_file_size_mb": 25,
    "max_merge_total_mb": 50
  }
  ```

### 2.3. `GET /api/files/conversions/history`
**Descrição:** Retorna as últimas conversões realizadas pelo usuário ativo.

- **Query Params:** `limit: int = 10`
- **Resposta `200 OK`:** Lista de registros de auditoria da coleção `file_conversions`.

---

## 3. Tool Function Calling (Gemini): `converter_arquivo`

**Nome:** `converter_arquivo`  
**Descrição:** Informa formatos suportados, instruções de conversão e processa operações de conversão solicitadas pelo usuário.

**Parâmetros de Entrada:**
- `acao` (string, obrigatório): `"listar_formatos"` | `"instrucoes"` | `"converter"`.
- `tipo_conversao` (string, opcional): Um dos tipos suportados (`pdf_para_word`, `word_para_pdf`, `fotos_para_pdf`, `juntar_pdfs`, `dividir_pdf`, `pdf_para_fotos`, `converter_imagem`, `extrair_texto`).
- `parametros` (string, opcional): Parâmetros adicionais (ex: páginas para dividir `"1-3"`, formato de destino `"PNG"`).

**Retorno:**
Texto em Markdown formatado para o WhatsApp instruindo o usuário a anexar o arquivo ou confirmando a conversão realizada.
