"""
Configurações centrais do backend.
Todos os valores sensíveis vêm de variáveis de ambiente (.env).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- JWT / Autenticação de usuários (dashboard) ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # --- Usuário admin único (sem banco de dados) ---
    # ADMIN_PASSWORD_HASH deve ser gerado com scripts/generate_password_hash.py
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")

    # --- Chave de API para os dispositivos ESP32 (não é usuário/senha) ---
    DEVICE_API_KEY: str = os.getenv("DEVICE_API_KEY", "troque-esta-chave-de-dispositivo")

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")


settings = Settings()
