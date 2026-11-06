from cryptography.fernet import Fernet, InvalidToken

from backend.app.core.config import settings


class SecretStoreError(RuntimeError):
    pass


def _fernet() -> Fernet:
    if not settings.encryption_key:
        raise SecretStoreError(
            "MERGEMIND_ENCRYPTION_KEY is missing. Run: python -m backend.app.cli init"
        )
    try:
        return Fernet(settings.encryption_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise SecretStoreError("MERGEMIND_ENCRYPTION_KEY is not a valid Fernet key") from exc


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise SecretStoreError("Could not decrypt a stored secret; check the encryption key") from exc
