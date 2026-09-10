import json
import logging
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional
from config.settings import settings
from repositories.address_repository import AddressRepository, normalize_alias

logger = logging.getLogger(__name__)


def geocodificar_endereco(endereco: str) -> Dict[str, Any]:
    """Queries the Google Maps Geocoding API to normalize the address and obtain coordinates."""
    if not endereco:
        return {"formatted_address": "", "latitude": None, "longitude": None}

    if settings.GOOGLE_MAPS_API_KEY:
        try:
            url = (
                "https://maps.googleapis.com/maps/api/geocode/json?"
                f"address={urllib.parse.quote(endereco)}&"
                f"key={settings.GOOGLE_MAPS_API_KEY}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "DAM-Assistant/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))

            if data.get("status") == "OK" and data.get("results"):
                primeiro = data["results"][0]
                formatted = primeiro.get("formatted_address", endereco)
                loc = primeiro.get("geometry", {}).get("location", {})
                lat = loc.get("lat")
                lng = loc.get("lng")
                return {
                    "formatted_address": formatted,
                    "latitude": lat,
                    "longitude": lng
                }
        except Exception as e:
            logger.warning(f"[AddressTool] Falha ao geocodificar '{endereco}': {e}. Usando texto direto.")

    return {
        "formatted_address": endereco.strip(),
        "latitude": None,
        "longitude": None
    }


def salvar_endereco(apelido: str, endereco: str, detalhes: str = "", user_jid: str = "") -> str:
    """Saves or updates a frequently used address or favorite location in the database."""
    clean_alias = normalize_alias(apelido)
    if not clean_alias:
        return "Erro: É necessário informar um apelido para o local (ex: 'casa', 'trabalho', 'academia')."

    if not endereco or not endereco.strip():
        return "Erro: O endereço completo precisa ser informado."

    # Geocodifica para obter coordenadas e endereço formatado
    geo = geocodificar_endereco(endereco)
    formatted_addr = geo.get("formatted_address") or endereco.strip()
    lat = geo.get("latitude")
    lng = geo.get("longitude")

    res = AddressRepository.save_address(
        user_jid=user_jid,
        alias=clean_alias,
        address=endereco.strip(),
        formatted_address=formatted_addr,
        latitude=lat,
        longitude=lng,
        details=detalhes.strip() if detalhes else ""
    )

    detalhe_str = f" ({detalhes})" if detalhes else ""
    coords_str = f" [Lat: {lat}, Lng: {lng}]" if lat is not None else ""
    return (
        f"📍 Endereço '{clean_alias}' salvo com sucesso no banco de dados!\n"
        f"• Endereço: {formatted_addr}{detalhe_str}{coords_str}\n"
        f"Você agora pode pedir rotas usando apenas o apelido (ex: 'tempo de {clean_alias} para o trabalho')."
    )


def consultar_enderecos_salvos(apelido: str = "", user_jid: str = "") -> str:
    """Queries the list of saved addresses and favorite locations or searches for a specific alias."""
    if apelido:
        clean_alias = normalize_alias(apelido)
        dado = AddressRepository.get_address(user_jid, clean_alias)
        if not dado:
            return f"Nenhum endereço encontrado para o apelido '{clean_alias}'."
        
        detalhe_str = f"\n  Detalhes: {dado['details']}" if dado.get("details") else ""
        return (
            f"📍 Endereço salvo: *{dado['alias'].title()}*\n"
            f"  Endereço: {dado.get('formatted_address') or dado.get('address')}"
            f"{detalhe_str}"
        )

    enderecos = AddressRepository.list_addresses(user_jid)
    if not enderecos:
        return "Nenhum endereço salvo encontrado. Você pode cadastrar dizendo, por exemplo: 'Salve o endereço de casa como Rua Tal, 123'."

    linhas = ["📍 *Seus Endereços Salvos:*"]
    for item in sorted(enderecos, key=lambda x: x.get("alias", "")):
        alias = item.get("alias", "").title()
        addr = item.get("formatted_address") or item.get("address", "")
        det = f" ({item['details']})" if item.get("details") else ""
        linhas.append(f"• *{alias}:* {addr}{det}")

    return "\n".join(linhas)


def remover_endereco(apelido: str, user_jid: str = "") -> str:
    """Removes a registered address or favorite location by its alias."""
    clean_alias = normalize_alias(apelido)
    if not clean_alias:
        return "Erro: Informe o apelido do endereço a ser removido."

    sucesso = AddressRepository.delete_address(user_jid, clean_alias)
    if sucesso:
        return f"🗑️ Endereço '{clean_alias}' removido com sucesso dos seus locais salvos."
    else:
        return f"Falha ao remover o endereço '{clean_alias}'."
