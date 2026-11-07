import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from config import firebase
from config.timezone import TZ_BRASILIA, get_brasilia_now, to_brasilia
from services.user_context import UserContext

logger = logging.getLogger(__name__)


class ChatRepository:
    COLLECTION = "chat_logs"
    COMPACTED_COLLECTION = "chat_history_compacted"

    @staticmethod
    def _is_daily_briefing_message(text: str, from_me: bool) -> bool:
        """Identifica mensagens de resumo matinal/diário emitidas pelo bot para exclusão da compactação."""
        if not text or not from_me:
            return False
        clean = text.strip()
        return (
            clean.startswith("🌅") 
            or "DAM Briefing Matinal" in clean 
            or "Briefing Matinal" in clean
        )

    @staticmethod
    def save_log(remote_jid: str, from_me: bool, text: str, message_id: str = None):
        if firebase.db is None:
            logger.warning("Firebase não inicializado, pulando salvamento de log.")
            return

        try:
            now_utc = datetime.now(timezone.utc)
            user_id = UserContext.get_user_id() or "daniel"
            doc_data = {
                "remoteJid": remote_jid,
                "userId": user_id,
                "fromMe": from_me,
                "text": text,
                "timestamp": now_utc
            }
            if message_id:
                doc_data["messageId"] = message_id

            firebase.db.collection(ChatRepository.COLLECTION).add(doc_data)
        except Exception as e:
            logger.exception("Erro ao salvar chat log no Firestore")

    @staticmethod
    def compact_and_archive_history(
        remote_jid: str,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compacta e arquiva o histórico de chat de dias anteriores a hoje (00:00 BRT).
        Exclui mensagens de resumo matinal/diário antes de salvar.
        Salva o histórico indexado na coleção 'chat_history_compacted'.
        """
        if firebase.db is None:
            return {"status": "skipped", "reason": "db_unavailable"}

        try:
            now_br = get_brasilia_now()
            today_start_br = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
            user_id = UserContext.get_user_id() or "daniel"

            # Se não especificou target_date, compacta o dia anterior
            if not target_date:
                target_date = (now_br - timedelta(days=1)).strftime("%Y-%m-%d")

            # Busca logs do remote_jid
            docs_query = (
                firebase.db.collection(ChatRepository.COLLECTION)
                .where("remoteJid", "==", remote_jid)
                .where("timestamp", "<", today_start_br)
                .stream()
            )

            mensagens_alvo = []
            for d in docs_query:
                data = d.to_dict()
                ts = data.get("timestamp")
                if not ts:
                    continue
                dt_br = to_brasilia(ts) if hasattr(ts, "astimezone") else ts
                dt_str = dt_br.strftime("%Y-%m-%d") if hasattr(dt_br, "strftime") else str(dt_br)[:10]

                if dt_str == target_date:
                    texto = (data.get("text") or "").strip()
                    from_me = bool(data.get("fromMe"))
                    # Exclui o resumo matinal diário
                    if ChatRepository._is_daily_briefing_message(texto, from_me):
                        continue
                    mensagens_alvo.append((dt_br, from_me, texto))

            if not mensagens_alvo:
                return {"status": "empty", "message_count": 0, "date": target_date}

            # Ordena cronologicamente
            mensagens_alvo.sort(key=lambda x: x[0])

            # Compacta em formato estruturado
            linhas_compactadas = []
            for _, from_me, txt in mensagens_alvo:
                autor = "DAM" if from_me else "User"
                # Limita linhas longas
                resumo_linha = txt[:200] + "..." if len(txt) > 200 else txt
                linhas_compactadas.append(f"[{autor}]: {resumo_linha}")

            compacted_text = " | ".join(linhas_compactadas)
            doc_id = f"{remote_jid}__{target_date}".replace("/", "_")

            payload = {
                "remoteJid": remote_jid,
                "userId": user_id,
                "date": target_date,
                "compactedText": compacted_text,
                "messageCount": len(mensagens_alvo),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }

            firebase.db.collection(ChatRepository.COMPACTED_COLLECTION).document(doc_id).set(payload)
            logger.info(f"Histórico de chat compactado para [{remote_jid}] em {target_date}: {len(mensagens_alvo)} msgs.")

            return {
                "status": "success",
                "message_count": len(mensagens_alvo),
                "date": target_date,
                "doc_id": doc_id
            }
        except Exception as e:
            logger.exception("Erro ao compactar histórico de chat")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_recent_history(remote_jid: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera as mensagens de hoje (corte 00:00 no horário de Brasília).
        Se houver histórico compactado indexado dos dias anteriores, injeta-o como
        contexto anterior para preservar a continuidade de memória da IA.
        """
        if firebase.db is None:
            return []

        try:
            now_br = get_brasilia_now()
            today_start_br = now_br.replace(hour=0, minute=0, second=0, microsecond=0)

            # 1. Busca mensagens recentes ativas
            docs = (
                firebase.db.collection(ChatRepository.COLLECTION)
                .where("remoteJid", "==", remote_jid)
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            history = []
            for doc in docs:
                data = doc.to_dict()
                ts = data.get("timestamp")
                if ts:
                    ts_br = to_brasilia(ts) if hasattr(ts, "astimezone") else ts
                    if ts_br >= today_start_br:
                        history.append(data)

            history.reverse()

            # 2. Se o histórico ativo for pequeno ou inicial, busca o histórico compactado mais recente
            try:
                compacted_docs = (
                    firebase.db.collection(ChatRepository.COMPACTED_COLLECTION)
                    .where("remoteJid", "==", remote_jid)
                    .order_by("date", direction="DESCENDING")
                    .limit(1)
                    .stream()
                )
                for cdoc in compacted_docs:
                    cdata = cdoc.to_dict()
                    compacted_summary = cdata.get("compactedText")
                    if compacted_summary:
                        context_msg = {
                            "remoteJid": remote_jid,
                            "fromMe": False,
                            "text": f"[Histórico compactado dos dias anteriores]:\n{compacted_summary}",
                            "timestamp": today_start_br - timedelta(seconds=1)
                        }
                        history.insert(0, context_msg)
                        break
            except Exception as ce:
                logger.debug(f"Nenhum histórico compactado recuperado ou erro silencioso: {ce}")

            return history
        except Exception as e:
            logger.exception("Erro ao recuperar histórico recente no Firestore")
            return []
