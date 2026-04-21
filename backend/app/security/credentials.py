from cryptography.fernet import Fernet
from app.config import settings


def _fernet() -> Fernet:
    if not settings.fernet_key:
        raise RuntimeError("FERNET_KEY is not set. Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    return Fernet(settings.fernet_key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()


def get_device_credentials(device) -> dict:
    return {
        "username": device.username,
        "password": decrypt(device.password_encrypted) if device.password_encrypted else "",
        "secret": decrypt(device.enable_secret_encrypted) if device.enable_secret_encrypted else "",
        "snmp_community": decrypt(device.snmp_community_encrypted) if device.snmp_community_encrypted else "public",
    }
