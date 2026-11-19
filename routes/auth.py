"""
Rotas de autenticação: login, logout e status.
"""
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, jsonify
)

from services.supabase_service import autenticar, obter_perfil
from services.auth_guard import get_csrf_token, validar_csrf

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/status", methods=["GET"])
def status():
    return jsonify({
        "modulo": "auth",
        "status": "OK",
        "mensagem": "Blueprint de autenticação ativo.",
    })


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""
        csrf = request.form.get("csrf_token")

        if not validar_csrf(csrf):
            flash("Sessão expirada. Tente novamente.", "error")
            return redirect(url_for("auth.login"))

        if not email or not senha:
            flash("Informe e-mail e senha.", "error")
            return render_template(
                "login.html",
                csrf_token=get_csrf_token(),
                email=email,
            )

        try:
            resposta = autenticar(email, senha)
            user = resposta.user
            if not user:
                flash("E-mail ou senha incorretos.", "error")
                return render_template(
                    "login.html", csrf_token=get_csrf_token(), email=email
                )

            perfil = obter_perfil(user.id)
            if not perfil:
                flash("Perfil não encontrado. Procure a administração.", "error")
                return render_template(
                    "login.html", csrf_token=get_csrf_token(), email=email
                )
            if not perfil.get("ativo"):
                flash("Usuário desativado. Procure a administração.", "error")
                return render_template(
                    "login.html", csrf_token=get_csrf_token(), email=email
                )

            # Cria sessão
            session.clear()
            session["user_id"] = user.id
            session["email"] = user.email
            session["nome"] = perfil["nome_completo"]
            session["role"] = perfil["role"]
            session.permanent = True

            flash(f"Bem-vindo(a), {perfil['nome_completo']}!", "success")
            return redirect(url_for("dashboard.index"))

        except Exception as e:
            msg = str(e).lower()
            if any(k in msg for k in ("invalid", "credential", "password", "user")):
                flash("E-mail ou senha incorretos.", "error")
            else:
                flash(f"Erro ao autenticar: {e}", "error")
            return render_template(
                "login.html", csrf_token=get_csrf_token(), email=email
            )

    return render_template("login.html", csrf_token=get_csrf_token(), email="")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))