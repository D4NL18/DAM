import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import logging
from .settings import settings

logger = logging.getLogger(__name__)

db = None


def _resolve_credentials_path() -> str:
    """Resolve o caminho de credenciais do Firebase mesmo quando executado fora do diretório backend_ia."""
    configured = settings.FIREBASE_CREDENTIALS_PATH
    if os.path.exists(configured):
        return configured
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fallback = os.path.join(backend_dir, os.path.basename(configured))
    if os.path.exists(fallback):
        return fallback
    return configured


def init_firebase():
    global db
    creds_path = _resolve_credentials_path()
    if not firebase_admin._apps:
        if not os.path.exists(creds_path):
            logger.warning(f"Aviso: Arquivo de credenciais do Firebase não encontrado em {creds_path}")
            return

        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase inicializado com sucesso!")
    elif db is None:
        db = firestore.client()
