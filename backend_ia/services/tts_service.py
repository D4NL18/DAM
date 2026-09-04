import hashlib
import logging
import re
import threading
import json
import os
import base64
import urllib.parse
import urllib.request
from typing import Optional, Dict
from config.settings import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Motor de Text-to-Speech (Síntese de Voz) com sanitização fonética e cache FinOps."""

    _cache: Dict[str, bytes] = {}
    _lock = threading.RLock()

    @classmethod
    def sanitize_text_for_speech(cls, text: str) -> str:
        """
        Remove formatações de markdown, links e emojis excessivos para garantir
        uma dicção natural e fluida pelo sintetizador fonético.
        """
        if not text:
            return ""

        # 1. Remove blocos de código
        limpo = re.sub(r"```[\s\S]*?```", "", text)
        limpo = re.sub(r"`[^`]*`", "", limpo)

        # 2. Substitui links por menção suave
        limpo = re.sub(r"https?://\S+", "o link compartilhado", limpo)

        # 3. Remove marcadores markdown (#, *, _, ~, >)
        limpo = re.sub(r"[#*_~>]", "", limpo)

        # 4. Remove emojis comuns (faixas unicode de emojis)
        emoji_pattern = re.compile(
            r"[\U00010000-\U0010ffff"
            r"\u2600-\u27bf"
            r"\u2300-\u23ff"
            r"\u2b50\u2b55\u2934\u2935"
            r"\u200d\ufe0f]",
            flags=re.UNICODE
        )
        limpo = emoji_pattern.sub("", limpo)

        # 5. Converte listas com bullets em pausas naturais
        limpo = re.sub(r"^\s*[-•]\s+", ", ", limpo, flags=re.MULTILINE)

        # 6. Normaliza múltiplos espaços e quebras de linha
        limpo = re.sub(r"\n+", ". ", limpo)
        limpo = re.sub(r"\s+", " ", limpo).strip()
        limpo = re.sub(r"\s+([,.?!])", r"\1", limpo)
        limpo = re.sub(r"([,.?!]){2,}", r"\1", limpo)

        return limpo

    @classmethod
    def should_reply_with_audio(cls, incoming_text: str = "", message_type: str = "conversation") -> bool:
        """
        Determina se a resposta da IA deve ser enviada como áudio (PTT/Voz).
        Gatilhos:
        1. Se a mensagem recebida for um áudio ('audioMessage').
        2. Se o usuário pedir expressamente resposta em áudio no texto.
        """
        if message_type in ["audioMessage", "audio"]:
            return True

        if not incoming_text:
            return False

        padrao_voz = (
            r"\b(em áudio|em audio|por áudio|por audio|por voz|grave um áudio|grave um audio|"
            r"mande áudio|mande audio|me manda áudio|me manda audio|fale para mim|fale pra mim|"
            r"leia para mim|leia pra mim|responde por voz|responda por voz|responde por áudio|"
            r"responda por áudio|responde por audio|responda por audio|"
            r"converte.*(áudio|audio)|converta.*(áudio|audio)|converter.*(áudio|audio)|"
            r"transforma.*(áudio|audio)|transforme.*(áudio|audio)|transformar.*(áudio|audio)|"
            r"passa.*(áudio|audio)|passe.*(áudio|audio)|passar.*(áudio|audio)|"
            r"gerar.*(áudio|audio)|gere.*(áudio|audio)|gera.*(áudio|audio)|"
            r"manda.*(áudio|audio)|mande.*(áudio|audio)|enviar.*(áudio|audio)|envie.*(áudio|audio)|"
            r"voz alta|ler em voz alta|leia em voz alta|reproduza em áudio|reproduza em audio|"
            r"áudio dessa|audio dessa|áudio desta|audio desta|áudio disso|audio disso)\b"
        )
        return bool(re.search(padrao_voz, incoming_text, re.IGNORECASE))

    @classmethod
    def _quebrar_em_chunks(cls, text: str, max_chars: int = 160) -> list[str]:
        """Divide o texto em pedaços menores de até max_chars respeitando pontuação."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        # Divide mantendo os delimitadores de pontuação
        partes = re.split(r'([.!?,;]+)', text)
        atual = ""

        for p in partes:
            if not p:
                continue
            if len(atual) + len(p) <= max_chars:
                atual += p
            else:
                if atual.strip():
                    chunks.append(atual.strip())
                # Se uma única parte for maior que max_chars, fatia por palavras
                if len(p) > max_chars:
                    palavras = p.split()
                    sub = ""
                    for w in palavras:
                        if len(sub) + len(w) + 1 <= max_chars:
                            sub = f"{sub} {w}".strip()
                        else:
                            if sub:
                                chunks.append(sub)
                            sub = w
                    atual = sub
                else:
                    atual = p

        if atual.strip():
            chunks.append(atual.strip())

        return chunks if chunks else [text[:max_chars]]

    @classmethod
    def _gerar_audio_cloud_tts(cls, text: str) -> Optional[bytes]:
        """
        Sintetiza via Google Cloud Text-to-Speech API oficial com a voz pt-BR-Chirp3-HD-Aoede.
        Retorna os bytes em MP3 ou None se credenciais indisponíveis.
        """
        import os
        import base64
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidatos = [
            os.path.join(base_dir, "dam-tts-key.json"),
            "/app/dam-tts-key.json",
            os.path.join(base_dir, "firebase-adminsdk.json"),
            "/app/firebase-adminsdk.json"
        ]
        key_file = next((c for c in candidatos if os.path.exists(c)), None)
        if not key_file:
            return None

        try:
            from google.oauth2 import service_account
            import google.auth.transport.requests

            creds = service_account.Credentials.from_service_account_file(
                key_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            token = creds.token
            if not token:
                return None

            url = "https://texttospeech.googleapis.com/v1/text:synthesize"
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": "pt-BR",
                    "name": "pt-BR-Chirp3-HD-Aoede"
                },
                "audioConfig": {
                    "audioEncoding": "MP3"
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                b64 = data.get("audioContent", "")
                if b64:
                    return base64.b64decode(b64)
        except Exception as e:
            logger.warning(f"[TTSService] Falha ao sintetizar via Cloud TTS (pt-BR-Chirp3-HD-Aoede): {e}")

        return None

    @classmethod
    def _gerar_audio_provedor(cls, text: str) -> bytes:
        """
        Gera o áudio através de serviço TTS.
        Primeira escolha: Google Cloud Text-to-Speech oficial com voz pt-BR-Chirp3-HD-Aoede.
        Fallback resiliente: Fatiamento em chunks de até 160 caracteres.
        """
        # 1. Tentativa primária: Google Cloud TTS com pt-BR-Chirp3-HD-Aoede
        audio_chirp = cls._gerar_audio_cloud_tts(text)
        if audio_chirp:
            logger.info("[TTSService] Voz pt-BR-Chirp3-HD-Aoede sintetizada com sucesso via Cloud TTS!")
            return audio_chirp

        # 2. Fallback: Síntese fonética particionada
        chunks = cls._quebrar_em_chunks(text, max_chars=160)
        audio_blocos = []

        for chunk in chunks:
            if not chunk.strip():
                continue
            url = (
                "https://translate.google.com/translate_tts?ie=UTF-8&tl=pt-BR&client=tw-ob&q="
                f"{urllib.parse.quote(chunk)}"
            )
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                audio_data = response.read()
                if audio_data:
                    audio_blocos.append(audio_data)

        if not audio_blocos:
            raise ValueError("Resposta de áudio vazia do provedor TTS")

        return b"".join(audio_blocos)



    @classmethod
    def synthesize_speech(cls, text: str) -> Optional[bytes]:
        """
        Sintetiza texto em áudio com cache L1 FinOps para reutilização de áudios idênticos.
        """
        texto_limpo = cls.sanitize_text_for_speech(text)
        if not texto_limpo:
            return None

        # Chave determinística de cache FinOps
        cache_key = hashlib.sha256(texto_limpo.encode("utf-8")).hexdigest()

        with cls._lock:
            if cache_key in cls._cache:
                logger.info("[TTSService] Cache HIT FinOps: Reutilizando áudio sintetizado.")
                return cls._cache[cache_key]

        try:
            audio_bytes = cls._gerar_audio_provedor(texto_limpo)
            with cls._lock:
                cls._cache[cache_key] = audio_bytes
            logger.info(f"[TTSService] Áudio sintetizado com sucesso ({len(audio_bytes)} bytes).")
            return audio_bytes
        except Exception as e:
            logger.error(f"[TTSService] Falha ao sintetizar voz: {e}")
            return None
