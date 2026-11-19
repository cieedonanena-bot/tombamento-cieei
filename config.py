"""
Configurações centralizadas da aplicação.
Todos os valores sensíveis vêm de variáveis de ambiente (.env).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-insegura-troque")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = os.getenv("SESSION_COOKIE_HTTPONLY", "True").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 horas

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Validação básica na inicialização
    @classmethod
    def validar(cls):
        faltando = []
        if not cls.SUPABASE_URL:
            faltando.append("SUPABASE_URL")
        if not cls.SUPABASE_ANON_KEY:
            faltando.append("SUPABASE_ANON_KEY")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            faltando.append("SUPABASE_SERVICE_ROLE_KEY")
        if cls.SECRET_KEY == "chave-insegura-troque" or not cls.SECRET_KEY:
            faltando.append("SECRET_KEY (gere com secrets.token_urlsafe)")
        if faltando:
            raise RuntimeError(
                f"Variáveis de ambiente ausentes/ inválidas no .env: {', '.join(faltando)}"
            )