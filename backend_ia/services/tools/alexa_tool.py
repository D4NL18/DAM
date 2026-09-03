import logging
import urllib.request
import json
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)

VOICE_MONKEY_BASE_URL = "https://api-v3.voicemonkey.io"

def determinar_acao_e_device(rotina: str, ambiente: Optional[str] = None) -> tuple[str, str]:
    """
    Determina o dispositivo ('pc', 'tv', 'ar') e o estado ('open' para ligar, 'close' para desligar).
    Permite que 1 único trigger faça tanto Ligar quanto Desligar na Alexa via sensor de abertura.
    """
    r = rotina.strip().lower()
    
    # Detecta se é desligamento
    is_off = any(w in r for w in ["deslig", "apagar", "fechar", "parar"])
    state = "close" if is_off else "open"
    
    # 1. Computador / PC
    if "computador" in r or "pc" in r:
        return "pc", state

    # 2. TV
    if "tv" in r or "televis" in r:
        return "tv", state

    # 3. Ar-condicionado
    if any(w in r for w in [" ar", "ar-", "ar condicionado", "climatizador"]) or r.startswith("ar"):
        return "ar", state

    return r.replace("-", " "), state

def _resolver_device_id(target: str, token: str) -> str:
    """Busca o Device ID oficial do Voice Monkey a partir do nome (ex: 'pc' -> 'pc-0xvhr')."""
    try:
        req = urllib.request.Request(
            f"{VOICE_MONKEY_BASE_URL}/devices?token={token}",
            headers={"User-Agent": "DAM/1.0"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            devices = data.get("data", [])
            for dev in devices:
                if dev.get("name", "").strip().lower() == target.strip().lower():
                    return dev.get("id", target)
                if dev.get("id") == target:
                    return dev.get("id")
    except Exception as e:
        logger.warning(f"Não foi possível resolver device no Voice Monkey ({e}), usando nome direto.")
    return target

def acionar_rotina_alexa(rotina: str, ambiente: Optional[str] = None) -> str:
    """
    Aciona uma rotina ou dispositivo de automação residencial na Alexa via Voice Monkey API.
    Use quando o usuário pedir para ligar/desligar luzes, aparelhos ou iniciar cenas (ex: 'Ligar PC', 'Ligar TV', 'Desligar TV', 'Ligar Ar', 'Desligar Ar').

    Args:
        rotina (str): Nome da rotina, cena ou comando (ex: 'Ligar PC', 'Ligar TV', 'Desligar TV', 'Ligar Ar', 'Desligar Ar').
        ambiente (str, optional): Cômodo ou ambiente da casa (ex: 'Sala', 'Escritório', 'Quarto').
    """
    ambiente_str = f" no ambiente '{ambiente}'" if ambiente else ""
    token = settings.VOICE_MONKEY_API_TOKEN

    if token:
        target_name, state = determinar_acao_e_device(rotina, ambiente)
        device_id = _resolver_device_id(target_name, token)

        try:
            payload = {
                "device": device_id,
                "state": state
            }
            req = urllib.request.Request(
                f"{VOICE_MONKEY_BASE_URL}/trigger?token={token}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "DAM/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in [200, 201]:
                    acao_desc = "Desligando" if state == "close" else "Ligando"
                    logger.info(f"Voice Monkey Trigger executado: {device_id} [State: {state}]")
                    return f"Comando '{rotina}'{ambiente_str} executado com sucesso na sua Alexa! 💡"
        except urllib.error.HTTPError as he:
            body = he.read().decode("utf-8", errors="ignore")
            if "DEVICE_NOT_FOUND" in body:
                return (
                    f"Comando recebido! Porém, o gatilho virtual (Monkey) chamado **`{target_name}`** "
                    f"ainda não foi criado no seu painel [voicemonkey.io](https://voicemonkey.io).\n"
                    f"👉 Crie um Monkey com o nome `{target_name}` e vincule à rotina no app da Alexa!"
                )
            logger.error(f"Erro HTTP ao chamar Voice Monkey API: {body}")
            return f"Erro ao comunicar com a Alexa ({body})."
        except Exception as e:
            logger.error(f"Erro ao chamar Voice Monkey API: {e}")
            return f"Tentei acionar a rotina '{rotina}', mas ocorreu um erro: {e}"

    # Modo fallback / informativo se o token ainda não estiver no .env
    logger.info(f"Modo demonstração Alexa: Rotina '{rotina}'{ambiente_str}")
    return (
        f"Rotina '{rotina}'{ambiente_str} acionada em modo simulação! 💡\n"
        f"*(Adicione o `VOICE_MONKEY_API_TOKEN` no .env para disparar na Alexa física)*"
    )

def falar_na_alexa(mensagem: str, ambiente: Optional[str] = None) -> str:
    """
    Faz a Alexa falar uma frase ou aviso em voz alta na caixa de som do cômodo especificado.

    Args:
        mensagem (str): A frase ou anúncio a ser falado pela Alexa (ex: 'O almoço está pronto', 'Hora de tomar o remédio').
        ambiente (str, optional): Cômodo da casa (ex: 'Quarto', 'Sala', 'Cozinha').
    """
    token = settings.VOICE_MONKEY_API_TOKEN
    ambiente_str = f" no ambiente '{ambiente}'" if ambiente else ""

    if token:
        device_target = ambiente.strip().lower() if ambiente else "all"
        try:
            payload = {
                "device": device_target,
                "speech": mensagem
            }
            req = urllib.request.Request(
                f"{VOICE_MONKEY_BASE_URL}/announce?token={token}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "DAM/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in [200, 201]:
                    logger.info(f"Anúncio Alexa enviado: '{mensagem}'")
                    return f"Anúncio enviado com sucesso! A Alexa está falando{ambiente_str}: \"{mensagem}\" 📢"
        except urllib.error.HTTPError as he:
            body = he.read().decode("utf-8", errors="ignore")
            if "DEVICE_NOT_FOUND" in body:
                return (
                    f"Não encontrei o dispositivo de áudio **`{device_target}`** no seu Voice Monkey.\n"
                    f"Verifique o nome do Echo Dot no seu painel [voicemonkey.io](https://voicemonkey.io/devices)."
                )
            logger.error(f"Erro HTTP anúncio Voice Monkey: {body}")
            return f"Não consegui enviar o áudio para a Alexa: {body}"
        except Exception as e:
            logger.error(f"Erro ao enviar anúncio para a Alexa: {e}")
            return f"Não consegui enviar o áudio para a Alexa: {e}"

    return (
        f"Anúncio simulado! A Alexa falaria{ambiente_str}: \"{mensagem}\" 📢"
    )
