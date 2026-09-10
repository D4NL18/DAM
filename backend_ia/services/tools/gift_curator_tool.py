import re
import uuid
import logging
from typing import Optional, List
from datetime import datetime, timezone, date, timedelta
from config import firebase
from services.user_context import UserContext

logger = logging.getLogger(__name__)

# Armazenamento em memória (mock/fallback) quando o Firestore não estiver disponível
_MOCK_GIFT_IDEAS: List[dict] = []

def _reset_mock_gift_db():
    """Clears the mock list for unit tests."""
    global _MOCK_GIFT_IDEAS
    _MOCK_GIFT_IDEAS.clear()

def _parse_special_date(date_str: Optional[str]) -> Optional[date]:
    """
    Attempts to convert different date formats into a date object.
    Supports ISO, full Brazilian, and day/month formats.
    """
    if not date_str:
        return None
    cleaned = str(date_str).strip()

    # 1. Formato ISO YYYY-MM-DD
    match_iso = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', cleaned)
    if match_iso:
        y, m, d = int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3))
        try:
            return date(y, m, d)
        except ValueError:
            pass

    # 2. Formato Brasileiro DD/MM/YYYY
    match_br = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', cleaned)
    if match_br:
        d, m, y = int(match_br.group(1)), int(match_br.group(2)), int(match_br.group(3))
        try:
            return date(y, m, d)
        except ValueError:
            pass

    # 3. Formato Recorrente / Curto DD/MM
    match_short = re.search(r'(\d{1,2})[/-](\d{1,2})', cleaned)
    if match_short:
        d, m = int(match_short.group(1)), int(match_short.group(2))
        hoje = date.today()
        try:
            d_este_ano = date(hoje.year, m, d)
            # Se já passou há mais de 30 dias neste ano, projeta para o próximo
            if d_este_ano < hoje and (hoje - d_este_ano).days > 30:
                return date(hoje.year + 1, m, d)
            return d_este_ano
        except ValueError:
            pass

    return None

def salvar_ideia_presente(
    pessoa: str, 
    relacao: str, 
    ideia: str, 
    data_especial: Optional[str] = None, 
    tags: Optional[List[str]] = None
) -> str:
    """
    Registers a new gift idea for a special person.
    
    Args:
        pessoa (str): Name of the person to receive the gift.
        relacao (str): Relationship degree.
        ideia (str): Description of the gift idea.
        data_especial (str, optional): Associated special date.
        tags (list[str], optional): List of tags or categories.
    """
    if not pessoa or not pessoa.strip():
        return "Por favor, informe o nome da pessoa para salvar a ideia de presente."
    if not ideia or not ideia.strip():
        return "Por favor, descreva a ideia de presente a ser registrada."

    tags_limpas = [t.strip() for t in tags if t and t.strip()] if tags else []
    user_id = UserContext.get_user_id()

    record = {
        "id": str(uuid.uuid4()),
        "userId": user_id,
        "user_id": user_id,
        "pessoa": pessoa.strip(),
        "relacao": relacao.strip() if relacao else "Outro",
        "ideia": ideia.strip(),
        "data_especial": data_especial.strip() if data_especial else None,
        "tags": tags_limpas,
        "data_captura": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc)
    }

    saved_in_firestore = False
    if firebase.db is not None:
        try:
            firebase.db.collection("gift_ideas").add(record)
            saved_in_firestore = True
            logger.info(f"Ideia de presente salva no Firestore: {record['pessoa']} - {record['ideia']}")
        except Exception as e:
            logger.error(f"Erro ao salvar ideia de presente no Firestore: {e}. Usando fallback em memória.")
            _MOCK_GIFT_IDEAS.append(record)
    else:
        _MOCK_GIFT_IDEAS.append(record)
        logger.info(f"Ideia de presente salva em modo mock/fallback: {record['pessoa']} - {record['ideia']}")

    detalhes = [
        "🎁 *Ideia de presente anotada com sucesso!*",
        f"• *Pessoa:* {record['pessoa']} ({record['relacao']})",
        f"• *Ideia:* {record['ideia']}"
    ]
    if record["data_especial"]:
        detalhes.append(f"• *Data Especial:* {record['data_especial']}")
    if record["tags"]:
        detalhes.append(f"• *Tags:* {', '.join(record['tags'])}")

    if not saved_in_firestore and firebase.db is None:
        detalhes.append("_(Salvo em memória temporária - Firestore offline)_")

    return "\n".join(detalhes)

def consultar_ideias_presente(
    pessoa: Optional[str] = None, 
    relacao: Optional[str] = None
) -> str:
    """
    Queries saved gift ideas with contextual details.
    
    Args:
        pessoa (str, optional): Filter by person's name.
        relacao (str, optional): Filter by relationship degree.
    """
    todos: List[dict] = []
    
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("gift_ideas").stream()
            for doc in docs:
                data = doc.to_dict()
                todos.append(data)
        except Exception as e:
            logger.error(f"Erro ao consultar Firestore: {e}. Usando mock.")
            todos = list(_MOCK_GIFT_IDEAS)
    else:
        todos = list(_MOCK_GIFT_IDEAS)

    user_id = UserContext.get_user_id()
    # Retrocompatibilidade: sem userId assume daniel
    todos = [i for i in todos if (i.get("userId") or i.get("user_id") or "daniel") == user_id]

    filtrados = []
    for item in todos:
        p_match = True
        r_match = True
        if pessoa and pessoa.strip():
            p_match = pessoa.strip().lower() in item.get("pessoa", "").lower()
        if relacao and relacao.strip():
            r_match = relacao.strip().lower() in item.get("relacao", "").lower()
        if p_match and r_match:
            filtrados.append(item)

    if not filtrados:
        filtros_msg = []
        if pessoa:
            filtros_msg.append(f"pessoa '{pessoa}'")
        if relacao:
            filtros_msg.append(f"relação '{relacao}'")
        detalhe_filtro = f" para {' e '.join(filtros_msg)}" if filtros_msg else ""
        return f"Nenhuma ideia de presente encontrada{detalhe_filtro}."

    linhas = ["🎁 *Ideias de Presentes Encontradas:*", "━━━━━━━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(filtrados, 1):
        nome = item.get("pessoa", "Alguém")
        rel = item.get("relacao", "Geral")
        ideia_txt = item.get("ideia", "")
        data_esp = item.get("data_especial")
        tags = item.get("tags", [])

        linhas.append(f"*{i}. {nome}* ({rel})")
        linhas.append(f"   ↳ *Ideia:* {ideia_txt}")
        if data_esp:
            linhas.append(f"   ↳ *Data Especial:* {data_esp}")
        if tags:
            linhas.append(f"   ↳ *Tags:* {', '.join(tags)}")
        linhas.append("")

    return "\n".join(linhas).strip()

def alertar_datas_proximas(dias_antecedencia: int = 30) -> str:
    """
    Identifies registered special dates and birthdays within the next few days.
    
    Args:
        dias_antecedencia (int): Search window in days from today.
    """
    try:
        dias_limite = int(dias_antecedencia)
    except (ValueError, TypeError):
        dias_limite = 30

    todos: List[dict] = []
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("gift_ideas").stream()
            for doc in docs:
                todos.append(doc.to_dict())
        except Exception as e:
            logger.error(f"Erro ao consultar datas no Firestore: {e}")
            todos = list(_MOCK_GIFT_IDEAS)
    else:
        todos = list(_MOCK_GIFT_IDEAS)

    user_id = UserContext.get_user_id()
    todos = [i for i in todos if (i.get("userId") or i.get("user_id") or "daniel") == user_id]

    hoje = date.today()
    limite = hoje + timedelta(days=dias_limite)

    alertas = []
    for item in todos:
        raw_date = item.get("data_especial")
        if not raw_date:
            continue
        parsed = _parse_special_date(raw_date)
        if not parsed:
            continue

        dias_restantes = (parsed - hoje).days
        if 0 <= dias_restantes <= dias_limite:
            alertas.append({
                "item": item,
                "data": parsed,
                "dias_restantes": dias_restantes
            })

    if not alertas:
        return (
            f"📅 Nenhuma data especial encontrada nos próximos {dias_limite} dias.\n"
            "Dica: Ao anotar presentes, adicione datas como 'Aniversário 15/10' para receber lembretes!"
        )

    # Ordenar por proximidade de dias
    alertas.sort(key=lambda x: x["dias_restantes"])

    linhas = [
        f"⏰ *Alerta de Datas Especiais Próximas (Próximos {dias_limite} dias):*",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]
    for alerta in alertas:
        it = alerta["item"]
        d = alerta["data"].strftime("%d/%m/%Y")
        rest = alerta["dias_restantes"]
        tempo_str = "hoje!" if rest == 0 else f"em {rest} dia{'s' if rest > 1 else ''}"

        linhas.append(f"🎉 *{it.get('pessoa')}* ({it.get('relacao', 'Especial')}) - *{d}* ({tempo_str})")
        linhas.append(f"   ↳ Ideia salva: \"{it.get('ideia')}\"")
        if it.get("tags"):
            linhas.append(f"   ↳ Tags: {', '.join(it.get('tags'))}")
        linhas.append("")

    linhas.append("━━━━━━━━━━━━━━━━━━━━━━")
    linhas.append("💡 *Dica:* Vale a pena providenciar o presente com antecedência para evitar atrasos na entrega!")

    return "\n".join(linhas).strip()
