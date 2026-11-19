"""
Rotas da Administração e Auditoria.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)

from services.auth_guard import admin_required, validar_csrf
from services.auditoria import listar_historico
from services.transferencia_service import (
    listar_pendentes, aprovar_transferencia, rejeitar_transferencia
)
from services.funcionario_service import listar_funcionarios

administracao_bp = Blueprint("administracao", __name__, url_prefix="/administracao")


@administracao_bp.route("/")
@admin_required
def index():
    historico = listar_historico(limite=50)
    transferencias = listar_pendentes()
    funcionarios = listar_funcionarios()

    return render_template(
        "administracao.html",
        historico=historico,
        transferencias=transferencias,
        funcionarios=funcionarios,
    )


@administracao_bp.route("/transferencia/<sol_id>/aprovar", methods=["POST"])
@admin_required
def aprovar(sol_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("administracao.index"))

    try:
        aprovar_transferencia(sol_id, session["user_id"])
        flash("Transferência aprovada.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("administracao.index"))


@administracao_bp.route("/transferencia/<sol_id>/rejeitar", methods=["POST"])
@admin_required
def rejeitar(sol_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("administracao.index"))

    try:
        rejeitar_transferencia(
            sol_id, session["user_id"],
            request.form.get("justificativa", "")
        )
        flash("Transferência rejeitada.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("administracao.index"))