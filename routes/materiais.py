"""
Rotas do catálogo de materiais.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash
)

from services.auth_guard import login_required, admin_required, validar_csrf
from services.material_service import (
    listar_materiais, obter_material, criar_material,
    editar_material, alternar_ativo,
)

materiais_bp = Blueprint("materiais", __name__, url_prefix="/materiais")


@materiais_bp.route("/")
@login_required
def index():
    filtro = request.args.get("filtro", "ativos")
    incluir_inativos = filtro == "todos"
    materiais = listar_materiais(incluir_inativos=incluir_inativos)

    if filtro == "ativos":
        materiais = [m for m in materiais if m["ativo"]]
    elif filtro == "inativos":
        materiais = [m for m in materiais if not m["ativo"]]

    stats = {
        "total": len(materiais),
        "ativos": sum(1 for m in materiais if m["ativo"]),
        "inativos": sum(1 for m in materiais if not m["ativo"]),
    }

    return render_template(
        "materiais.html",
        materiais=materiais,
        filtro=filtro,
        stats=stats,
    )


@materiais_bp.route("/novo", methods=["GET", "POST"])
@admin_required
def novo():
    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada. Tente novamente.", "error")
            return redirect(url_for("materiais.novo"))

        try:
            criar_material(nome=request.form.get("nome", ""))
            flash("Material criado com sucesso.", "success")
            return redirect(url_for("materiais.index"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "material_form.html",
                modo="novo",
                material={"nome": request.form.get("nome", "")},
            )

    return render_template("material_form.html", modo="novo", material={})


@materiais_bp.route("/<material_id>/editar", methods=["GET", "POST"])
@admin_required
def editar(material_id):
    material = obter_material(material_id)
    if not material:
        flash("Material não encontrado.", "error")
        return redirect(url_for("materiais.index"))

    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada. Tente novamente.", "error")
            return redirect(url_for("materiais.editar", material_id=material_id))

        try:
            editar_material(
                material_id=material_id,
                nome=request.form.get("nome", ""),
            )
            flash("Material atualizado com sucesso.", "success")
            return redirect(url_for("materiais.index"))
        except ValueError as e:
            flash(str(e), "error")
            material = {
                "id": material_id,
                "nome": request.form.get("nome", ""),
                "ativo": material["ativo"],
            }

    return render_template("material_form.html", modo="editar", material=material)


@materiais_bp.route("/<material_id>/alternar", methods=["POST"])
@admin_required
def alternar(material_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("materiais.index"))

    try:
        resultado = alternar_ativo(material_id)
        if resultado["ativo"]:
            flash("Material reativado.", "success")
        else:
            flash("Material desativado.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("materiais.index"))