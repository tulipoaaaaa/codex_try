import base64
import keyring
from cryptography.fernet import Fernet, InvalidToken

SERVICE_NAME = 'CryptoFinanceCorpusBuilder'
KEYRING_KEY = 'config_encryption_key'


def get_fernet_key() -> bytes:
    """Retrieve or generate a Fernet key, stored in the OS keyring."""
    key = keyring.get_password(SERVICE_NAME, KEYRING_KEY)
    if key is None:
        key = Fernet.generate_key().decode()
        keyring.set_password(SERVICE_NAME, KEYRING_KEY, key)
    return key.encode()


def encrypt_value(value: str) -> str:
    """Encrypt a string value using Fernet and return as base64 string."""
    f = Fernet(get_fernet_key())
    token = f.encrypt(value.encode())
    return token.decode()


def decrypt_value(token: str) -> str:
    """Decrypt a Fernet-encrypted base64 string value."""
    f = Fernet(get_fernet_key())
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        return '' 