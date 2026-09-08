import os
import secrets
import string
import base64
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from config import firebase
from config.settings import settings
from services.user_context import UserContext

logger = logging.getLogger(__name__)


# Salt fixo para derivação de chave simétrica quando gerada via PBKDF2/SHA-256
VAULT_SALT = b"dam_vault_secure_salt_pbkdf2_2026"

# Armazenamento em memória para fallback gracioso
_in_memory_vault: Dict[str, Dict[str, Any]] = {}

def _reset_memory():
    """Limpa o cofre em memória (usado para testes unitários)."""
    _in_memory_vault.clear()

def _get_cipher() -> Fernet:
    """
    Obtém instância do Fernet para criptografia simétrica AES-128/256 autenticada.
    Verifica chave direta em VAULT_ENCRYPTION_KEY ou deriva via PBKDF2/SHA-256 a partir de segredo base.
    """
    direct_key = os.getenv("VAULT_ENCRYPTION_KEY") or getattr(settings, "VAULT_ENCRYPTION_KEY", "")
    if direct_key:
        try:
            return Fernet(direct_key.encode() if isinstance(direct_key, str) else direct_key)
        except Exception:
            pass

    base_secret = (
        os.getenv("VAULT_SECRET_KEY")
        or getattr(settings, "VAULT_SECRET_KEY", "")
        or getattr(settings, "WEBHOOK_TOKEN", "DAM_MASTER_VAULT_KEY_2026")
    )
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=VAULT_SALT,
        iterations=100000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(base_secret.encode()))
    return Fernet(derived_key)

def _format_datetime(iso_str: Optional[str]) -> str:
    """Formata data ISO para exibição em pt-BR."""
    if not iso_str:
        return "data não informada"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return iso_str

def _mascarar_senha(senha: str) -> str:
    """
    Mascara a senha para exibição segura sem revelá-la por padrão.
    Exemplo: 'Abc123456z9' -> 'Abc****z9'
    """
    tam = len(senha)
    if tam <= 2:
        return "*" * tam
    elif tam <= 6:
        return senha[0] + "*" * (tam - 2) + senha[-1]
    else:
        prefixo = senha[:3]
        sufixo = senha[-2:]
        return f"{prefixo}****{sufixo}"

def gerar_senha_forte(tamanho: int = 16, incluir_simbolos: bool = True) -> str:
    """
    Gera uma senha aleatória e criptograficamente segura usando o módulo secrets.
    Garante presença de maiúsculas, minúsculas, dígitos e símbolos.

    Args:
        tamanho: Comprimento total da senha (mínimo 8 caracteres, padrão 16).
        incluir_simbolos: Se True, inclui símbolos especiais (!@#$%&*...).
    """
    tamanho = max(8, tamanho)

    maiusculas = string.ascii_uppercase
    minusculas = string.ascii_lowercase
    digitos = string.digits
    simbolos = "!@#$%&*_-+=?~"

    # Garante pelo menos um caractere de cada conjunto obrigatório
    caracteres = [
        secrets.choice(maiusculas),
        secrets.choice(minusculas),
        secrets.choice(digitos)
    ]

    alfabeto = maiusculas + minusculas + digitos
    if incluir_simbolos:
        caracteres.append(secrets.choice(simbolos))
        alfabeto += simbolos

    while len(caracteres) < tamanho:
        caracteres.append(secrets.choice(alfabeto))

    # Embaralhamento criptograficamente seguro
    sr = secrets.SystemRandom()
    sr.shuffle(caracteres)
    return "".join(caracteres)

def salvar_credencial(

    servico: str, 
    usuario: str, 
    senha: str, 
    notas: Optional[str] = None
) -> str:
    """
    Criptografa e armazena com segurança uma credencial no cofre (Firestore: vault_credentials).
    
    Args:
        servico: Nome do serviço ou site (ex: 'GitHub', 'Banco Inter', 'Netflix').
        usuario: Nome de usuário, e-mail ou login.
        senha: Senha em texto plano a ser criptografada antes de salvar.
        notas: Informações contextuais opcionais (ex: 'Conta corporativa').
    """
    if not servico or not servico.strip():
        return "Por favor, informe o nome do serviço para salvar no cofre."
    if not usuario or not usuario.strip():
        return "Por favor, informe o usuário/e-mail associado à credencial."
    if not senha or not senha.strip():
        return "Por favor, informe a senha a ser armazenada."

    user_id = UserContext.get_user_id()
    servico_limpo = servico.strip()
    usuario_limpo = usuario.strip()
    senha_limpa = senha.strip()
    notas_limpas = notas.strip() if notas else None
    servico_key = servico_limpo.lower()
    doc_key = servico_key if user_id == "daniel" else f"{user_id}__{servico_key}"
    agora_iso = datetime.now(timezone.utc).isoformat()

    try:
        cipher = _get_cipher()
        senha_cripto = cipher.encrypt(senha_limpa.encode()).decode()
    except Exception as e:
        logger.error(f"Erro ao criptografar senha para {servico_limpo}: {e}")
        return "Erro ao criptografar a credencial. Ação cancelada por segurança."

    registro = {
        "userId": user_id,
        "user_id": user_id,
        "servico": servico_limpo,
        "servico_lower": servico_key,
        "usuario": usuario_limpo,
        "senha_criptografada": senha_cripto,
        "notas": notas_limpas,
        "atualizado_em": agora_iso
    }

    _in_memory_vault[doc_key] = registro
    if user_id == "daniel":
        _in_memory_vault[f"daniel__{servico_key}"] = registro

    # 1. Firestore
    if firebase.db is not None:
        try:
            firebase.db.collection("vault_credentials").document(doc_key).set(registro)
            logger.info(f"Credencial para '{servico_limpo}' de [{user_id}] salva no Firestore.")
            resp = f"🔒 Credencial para **{servico_limpo}** criptografada e salva com sucesso no cofre!"
            if notas_limpas:
                resp += f"\n• Notas: {notas_limpas}"
            return resp
        except Exception as e:
            logger.warning(f"Erro ao salvar no Firestore, usando fallback em memória: {e}")


    # 2. Fallback em memória
    resp = f"🔒 Credencial para **{servico_limpo}** criptografada e salva no cofre (memória)!"
    if notas_limpas:
        resp += f"\n• Notas: {notas_limpas}"
    return resp

def consultar_credencial(servico: str, revelar_senha: bool = False) -> str:
    """
    Recupera uma credencial do cofre do usuário ativo.
    """
    if not servico or not servico.strip():
        return "Por favor, informe o nome do serviço que deseja consultar."

    user_id = UserContext.get_user_id()
    termo = servico.strip().lower()
    doc_key = f"{user_id}__{termo}"
    registro = None

    # 1. Firestore
    if firebase.db is not None:
        try:
            # Busca direta pela chave particionada
            doc_ref = firebase.db.collection("vault_credentials").document(doc_key)
            doc_snap = doc_ref.get()
            if doc_snap.exists:
                registro = doc_snap.to_dict()
            elif user_id == "daniel":
                # Retrocompatibilidade para Daniel
                doc_legacy = firebase.db.collection("vault_credentials").document(termo).get()
                if doc_legacy.exists:
                    registro = doc_legacy.to_dict()

            if not registro:
                docs = firebase.db.collection("vault_credentials").stream()
                for d in docs:
                    data = d.to_dict() or {}
                    d_user = data.get("userId") or data.get("user_id") or "daniel"
                    if d_user == user_id and termo in data.get("servico_lower", ""):
                        registro = data
                        break
        except Exception as e:
            logger.warning(f"Erro ao buscar no Firestore: {e}")

    # 2. Fallback em memória
    if not registro:
        if doc_key in _in_memory_vault:
            registro = _in_memory_vault[doc_key]
        elif user_id == "daniel" and termo in _in_memory_vault:
            registro = _in_memory_vault[termo]
        else:
            for k, it in _in_memory_vault.items():
                d_user = it.get("userId") or it.get("user_id") or "daniel"
                if d_user == user_id and termo in it.get("servico_lower", ""):
                    registro = it
                    break

    if not registro:
        return f"Nenhuma credencial encontrada para o serviço '{servico}' no seu cofre."

    # Descriptografia
    try:
        cipher = _get_cipher()
        senha_plana = cipher.decrypt(registro["senha_criptografada"].encode()).decode()
    except Exception as e:
        logger.error(f"Erro ao descriptografar credencial de {registro.get('servico')}: {e}")
        return "Erro de integridade ou chave incorreta ao descriptografar a senha."

    nome_servico = registro.get("servico")
    usuario = registro.get("usuario")
    notas = registro.get("notas")
    data_formatada = _format_datetime(registro.get("atualizado_em"))

    if revelar_senha:
        senha_exibida = f"`{senha_plana}` 🔓"
    else:
        senha_exibida = f"`{_mascarar_senha(senha_plana)}` 🔒 *(use revelar_senha=True para exibir)*"

    linhas = [
        f"🔐 **Cofre de Senhas - {nome_servico}**",
        f"• **Usuário**: `{usuario}`",
        f"• **Senha**: {senha_exibida}",
        f"• **Última Atualização**: {data_formatada}"
    ]
    if notas:
        linhas.append(f"• **Notas**: {notas}")

    return "\n".join(linhas)

def listar_servicos_cofre() -> str:
    """
    Lista todos os serviços cadastrados no cofre seguro do usuário ativo.
    """
    user_id = UserContext.get_user_id()
    servicos: List[Dict[str, Any]] = []

    # 1. Firestore
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("vault_credentials").stream()
            for d in docs:
                data = d.to_dict() or {}
                d_user = data.get("userId") or data.get("user_id") or "daniel"
                if d_user == user_id:
                    servicos.append(data)
        except Exception as e:
            logger.warning(f"Erro ao listar do Firestore: {e}")

    # 2. Se vazio ou Firestore ausente, usa memória
    if not servicos and _in_memory_vault:
        for k, it in _in_memory_vault.items():
            d_user = it.get("userId") or it.get("user_id") or "daniel"
            if d_user == user_id:
                servicos.append(it)

    if not servicos:
        return "Seu cofre de senhas está vazio. Nenhuma credencial cadastrada no momento."

    linhas = ["🔐 **Serviços Cadastrados no seu Cofre Seguro:**"]
    for idx, item in enumerate(servicos, 1):
        srv = item.get("servico", "Desconhecido")
        user = item.get("usuario", "N/A")
        atualizado = _format_datetime(item.get("atualizado_em"))
        linhas.append(f"{idx}. **{srv}** (Usuário: `{user}`) - Atualizado em {atualizado}")

    linhas.append("\n*(Para consultar detalhes de um serviço, use a busca de credenciais)*")
    return "\n".join(linhas)

