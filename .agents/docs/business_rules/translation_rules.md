# Regras de Negócio: Tradutor Universal Multimodal (US-10)

## Visão Geral
Este documento define as regras canônicas de negócio que regem o serviço de tradução universal multimodal no DAM, integrando a Google Cloud Translation API no plano gratuito para processar textos, imagens e áudios com saída exclusivamente textual.

---

## Regras Canônicas (Padrão P-10XX)

### P-1001: Suporte Universal Any-to-Any e Detecção Automática
- O sistema **DEVE** traduzir de qualquer idioma para qualquer idioma suportado pela Google Cloud Translation API (mais de 100 idiomas).
- Se o idioma de origem não for informado explicitamente pelo usuário, o sistema **DEVE** realizar a detecção automática do idioma de origem (`detect_language` ou `source=None`).
- Se o idioma de destino não for especificado pelo usuário (ex: o usuário apenas diz "Traduza isso" ou envia um print em idioma estrangeiro), o idioma de destino padrão **DEVE** ser o Português (`pt`). Caso o usuário especifique um destino (ex: "traduza para o alemão"), o sistema **DEVE** traduzir para o idioma indicado.

### P-1002: FinOps & Preservação Estrita do Free Tier (500k caracteres/mês)
- A Google Cloud Translation API Basic oferece 500.000 caracteres gratuitos por mês calendário.
- O sistema **DEVE** manter o rastreamento mensal do total de caracteres traduzidos para cada mês (`YYYY-MM`).
- O sistema **DEVE** impor uma trava de segurança (*Hard Cap*) de 500.000 caracteres/mês. Se o limite for atingido, chamadas pagas da API do Google Cloud **NUNCA DEVEM** ser realizadas sem autorização explícita, ativando automaticamente o modo fallback de custo zero ou notificando o usuário.

### P-1003: Saída Estritamente em Formato Textual
- Toda e qualquer tradução gerada pelo DAM **DEVE** ser entregue ao usuário **SEMPRE em formato de texto legível**.
- Mesmo quando a entrada for um arquivo ou nota de voz de **áudio**, o sistema **DEVE suprimir** o envio de áudio sintetizado no WhatsApp (`deve_enviar_audio = False`), garantindo que o usuário receba a resposta transcrita e traduzida em texto para possibilitar leitura, cópia e consulta.

### P-1004: Processamento Multimodal (Imagens e Áudios)
- **Imagens:** Ao receber uma imagem com pedido de tradução (ou imagem contendo texto legível em língua estrangeira), o sistema **DEVE** extrair o texto via OCR/visão computacional do modelo multimodal e submeter o texto extraído ao motor de tradução.
- **Áudios:** Ao receber um áudio contendo fala em língua estrangeira ou comando solicitando tradução, o sistema **DEVE** transcrever o áudio e submeter a transcrição ao motor de tradução.
- O retorno final **DEVE** indicar claramente o idioma identificado e o texto traduzido de forma limpa e objetiva.

### P-1005: Normalização e Mapeamento Tolerante de Idiomas
- O sistema **DEVE** aceitar códigos ISO 639-1 (ex: `en`, `es`, `fr`, `de`, `it`, `ja`, `zh`, `ru`, `pt`) e nomes em linguagem natural em português (ex: `português`, `inglês`, `espanhol`, `francês`, `alemão`, `italiano`, `japonês`, `mandarim`, `russo`, etc.).
- Entradas de código de idioma com sufixos regionais (ex: `pt-BR`, `en-US`, `es-ES`) **DEVEM** ser normalizadas automaticamente para os códigos base aceitos pela API.

### P-1006: Resiliência, Fallback de Custo Zero e Sanitização
- Se a chave da API do Google Cloud Translation não estiver configurada no ambiente ou houver indisponibilidade temporária na rede, o sistema **NÃO DEVE** quebrar; **DEVE** utilizar um mecanismo de fallback resiliente e gratuito para garantir a continuidade da experiência.
- O texto submetido à tradução **NÃO DEVE** expor chaves de API, senhas do cofre ou dados confidenciais do usuário.
