import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import logging
from .settings import settings

logger = logging.getLogger(__name__)

db = None

def init_firebase():
    global db
    if not firebase_admin._apps:
        if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            logger.warning(f"Aviso: Arquivo de credenciais do Firebase não encontrado em {settings.FIREBASE_CREDENTIALS_PATH}")
            return
        
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase inicializado com sucesso!")
