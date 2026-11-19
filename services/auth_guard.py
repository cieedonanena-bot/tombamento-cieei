"""
Decorators e utilitários de autenticação e CSRF.
"""
import secrets
from functools import wraps

from flask import session, redirect, url_for, flash


# ============= CSRF =============
def get_csrf_token() -> str:
    """Retorna (ou cria) o token CSRF da sessão atual."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def validar_csrf(token: str | None) -> bool:
    """Compara o token do form com o da sessão em tempo constante."""
    stored = session.get("_csrf")
    if not stored or not token:
        return False
    return secrets.compare_digest(stored, token)


# ============= Decorators =============
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Acesso restrito a administradores.", "error")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return wrapper