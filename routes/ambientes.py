"""
Rotas de gestão de ambientes.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)

from services.auth_guard import login_required, admin_required, validar_csrf
from services.ambiente_service import (
    listar_ambientes, obter_ambiente, criar_ambiente,
    editar_ambiente, iniciar_responsabilidade,
    finalizar_responsabilidade, reabrir_ambiente,
)
from services.funcionario_service import listar_funcionarios
from services.transferencia_service import solicitar_transferencia

ambientes_bp = Blueprint("ambientes", __name__, url_prefix="/ambientes")


@ambientes_bp.route("/")
@login_required
def index():
    filtro = request.args.get("status", "todos")
    ambientes = listar_ambientes()

    if filtro != "todos":
        ambientes = [a for a in ambientes if a["status"] == filtro]

    # Estatísticas rápidas
    todos = listar_ambientes()
    stats = {
        "total": len(todos),
        "pendente": sum(1 for a in todos if a["status"] == "pendente"),
        "em_andamento": sum(1 for a in todos if a["status"] == "em_andamento"),
        "concluido": sum(1 for a in todos if a["status"] == "concluido"),
    }

    # Lista de funcionários para o modal de transferência
    funcionarios = [f for f in listar_funcionarios() if f["ativo"]]

    return render_template(
        "ambientes.html",
        ambientes=ambientes,
        filtro=filtro,
        stats=stats,
        funcionarios=funcionarios,
    )


@ambientes_bp.route("/novo", methods=["GET", "POST"])
@admin_required
def novo():
    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada. Tente novamente.", "error")
            return redirect(url_for("ambientes.novo"))

        try:
            criar_ambiente(
                nome=request.form.get("nome", ""),
                bloco_setor=request.form.get("bloco_setor", ""),
                observacao=request.form.get("observacao", ""),
            )
            flash("Ambiente criado com sucesso.", "success")
            return redirect(url_for("ambientes.index"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "ambiente_form.html",
                modo="novo",
                ambiente={
                    "nome": request.form.get("nome", ""),
                    "bloco_setor": request.form.get("bloco_setor", ""),
                    "observacao": request.form.get("observacao", ""),
                },
            )

    return render_template("ambiente_form.html", modo="novo", ambiente={})


@ambientes_bp.route("/<ambiente_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(ambiente_id):
    ambiente = obter_ambiente(ambiente_id)
    if not ambiente:
        flash("Ambiente não encontrado.", "error")
        return redirect(url_for("ambientes.index"))

    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada. Tente novamente.", "error")
            return redirect(url_for("ambientes.editar", ambiente_id=ambiente_id))

        try:
            editar_ambiente(
                ambiente_id=ambiente_id,
                nome=request.form.get("nome", ""),
                bloco_setor=request.form.get("bloco_setor", ""),
                observacao=request.form.get("observacao", ""),
            )
            flash("Ambiente atualizado com sucesso.", "success")
            return redirect(url_for("ambientes.index"))
        except ValueError as e:
            flash(str(e), "error")
            ambiente = {
                "id": ambiente_id,
                "nome": request.form.get("nome", ""),
                "bloco_setor": request.form.get("bloco_setor", ""),
                "observacao": request.form.get("observacao", ""),
            }

    return render_template("ambiente_form.html", modo="editar", ambiente=ambiente)


@ambientes_bp.route("/<ambiente_id>/iniciar", methods=["POST"])
@login_required
def iniciar(ambiente_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("ambientes.index"))

    try:
        resultado = iniciar_responsabilidade(ambiente_id, session["user_id"])
        if resultado.get("ja_era_responsavel"):
            flash("Você já é o responsável por este ambiente.", "info")
        else:
            flash("Conferência iniciada. Você é o responsável agora.", "success")
        return redirect(url_for("ambientes.index"))
    except ValueError as e:
        flash(str(e).replace("\n", " — "), "error")
        return redirect(url_for("ambientes.index"))


@ambientes_bp.route("/<ambiente_id>/finalizar", methods=["POST"])
@login_required
def finalizar(ambiente_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("ambientes.index"))

    try:
        finalizar_responsabilidade(ambiente_id, session["user_id"])
        flash("Ambiente finalizado com sucesso.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("ambientes.index"))


@ambientes_bp.route("/<ambiente_id>/reabrir", methods=["POST"])
@admin_required
def reabrir(ambiente_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("ambientes.index"))

    justificativa = request.form.get("justificativa", "").strip()
    try:
        reabrir_ambiente(ambiente_id, session["user_id"], justificativa)
        flash("Ambiente reaberto com sucesso.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("ambientes.index"))


@ambientes_bp.route("/<ambiente_id>/transferir", methods=["POST"])
@login_required
def transferir(ambiente_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("ambientes.index"))

    try:
        solicitar_transferencia(
            ambiente_id=ambiente_id,
            solicitante_id=session["user_id"],
            destinatario_id=request.form.get("destinatario_id", ""),
            motivo=request.form.get("motivo", ""),
        )
        flash("Solicitação de transferência enviada ao administrador.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("ambientes.index"))