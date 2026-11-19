"""
Rotas para gestão de funcionários.
Somente administradores têm acesso.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)

from services.auth_guard import admin_required, validar_csrf
from services.funcionario_service import (
    listar_funcionarios, obter_funcionario, criar_funcionario,
    editar_funcionario, alternar_ativo, redefinir_senha,
)

funcionarios_bp = Blueprint("funcionarios", __name__, url_prefix="/funcionarios")


@funcionarios_bp.route("/")
@admin_required
def index():
    funcionarios = listar_funcionarios()
    return render_template("funcionarios.html", funcionarios=funcionarios)


@funcionarios_bp.route("/novo", methods=["GET", "POST"])
@admin_required
def novo():
    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada. Tente novamente.", "error")
            return redirect(url_for("funcionarios.novo"))

        try:
            criar_funcionario(
                email=request.form.get("email", ""),
                senha=request.form.get("senha", ""),
                nome_completo=request.form.get("nome_completo", ""),
                role=request.form.get("role", "funcionario"),
            )
            flash("Funcionário criado com sucesso.", "success")
            return redirect(url_for("funcionarios.index"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "funcionario_form.html",
                modo="novo",
                funcionario={
                    "email": request.form.get("email", ""),
                    "nome_completo": request.form.get("nome_completo", ""),
                    "role": request.form.get("role", "funcionario"),
                },
            )

    return render_template("funcionario_form.html", modo="novo", funcionario={})


@funcionarios_bp.route("/<usuario_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(usuario_id):
    funcionario = obter_funcionario(usuario_id)
    if not funcionario:
        flash("Funcionário não encontrado.", "error")
        return redirect(url_for("funcionarios.index"))

    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada. Tente novamente.", "error")
            return redirect(url_for("funcionarios.editar", usuario_id=usuario_id))

        try:
            editar_funcionario(
                usuario_id=usuario_id,
                nome_completo=request.form.get("nome_completo", ""),
                role=request.form.get("role", "funcionario"),
            )
            flash("Funcionário atualizado com sucesso.", "success")
            return redirect(url_for("funcionarios.index"))
        except ValueError as e:
            flash(str(e), "error")
            funcionario["nome_completo"] = request.form.get("nome_completo", "")
            funcionario["role"] = request.form.get("role", "funcionario")

    return render_template("funcionario_form.html", modo="editar", funcionario=funcionario)


@funcionarios_bp.route("/<usuario_id>/alternar", methods=["POST"])
@admin_required
def alternar(usuario_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("funcionarios.index"))

    # Impede que o admin se desative por acidente
    if usuario_id == session.get("user_id"):
        flash("Você não pode desativar seu próprio acesso.", "error")
        return redirect(url_for("funcionarios.index"))

    try:
        novo_estado = alternar_ativo(usuario_id)
        flash("Funcionário reativado." if novo_estado else "Funcionário desativado.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("funcionarios.index"))


@funcionarios_bp.route("/<usuario_id>/senha", methods=["POST"])
@admin_required
def senha(usuario_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("funcionarios.index"))

    try:
        redefinir_senha(usuario_id, request.form.get("nova_senha", ""))
        flash("Senha redefinida com sucesso.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("funcionarios.index"))