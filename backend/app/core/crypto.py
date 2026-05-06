"""
Utilitários de criptografia.

Todas as API keys de clientes (LLM, Z-API) são criptografadas com Fernet
antes de salvar no banco. Chaves nunca aparecem em logs.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _get_fernet() -> Fernet:
    return Fernet(settings.encryption_key.encode())


def encrypt(plaintext: str) -> str:
    """Criptografa uma string. Retorna o token Fernet como string."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Descriptografa um token Fernet. Levanta ValueError se inválido."""
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Token de criptografia inválido ou chave incorreta") from e


def mask(value: str, visible_chars: int = 4) -> str:
    """Mascara uma chave para logs. Ex: 'sk-ant-...' → 'sk-a****'."""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return value[:visible_chars] + "****"
