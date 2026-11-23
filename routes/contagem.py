"""
Rotas da contagem de materiais.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)
from services.auth_guard import login_required, validar_csrf
from services.ambiente_service import obter_ambiente
from services.contagem_service import (
    listar_grupos_por_ambiente, salvar_contagem, listar_marcas_modelos,
    obter_grupo, excluir_grupo
)
from services.material_service import listar_materiais

contagem_bp = Blueprint("contagem", __name__, url_prefix="/contagem")


@contagem_bp.route("/<ambiente_id>")
@login_required
def index(ambiente_id):
    ambiente = obter_ambiente(ambiente_id)
    if not ambiente:
        flash("Ambiente não encontrado.", "error")
        return redirect(url_for("ambientes.index"))

    grupos = listar_grupos_por_ambiente(ambiente_id)
    materiais = [m for m in listar_materiais() if m["ativo"]]

    total_itens = sum(g["quantidade_total"] for g in grupos)
    com_selo = sum(g["quantidade_com_selo"] for g in grupos)
    sem_selo = sum(g["quantidade_sem_selo"] for g in grupos)
    com_dano = sum(1 for g in grupos if g["tem_dano"])

    return render_template(
        "contagem.html",
        ambiente=ambiente,
        grupos=grupos,
        materiais=materiais,
        total_itens=total_itens,
        com_selo=com_selo,
        sem_selo=sem_selo,
        com_dano=com_dano,
    )


@contagem_bp.route("/<ambiente_id>/novo", methods=["GET", "POST"])
@login_required
def novo(ambiente_id):
    ambiente = obter_ambiente(ambiente_id)
    if not ambiente or ambiente["status"] != "em_andamento":
        flash("Este ambiente não está em andamento.", "error")
        return redirect(url_for("ambientes.index"))

    materiais = [m for m in listar_materiais() if m["ativo"]]
    sugestoes = listar_marcas_modelos()

    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada.", "error")
            return redirect(url_for("contagem.novo", ambiente_id=ambiente_id))

        try:
            material_id = request.form.get("material_id")
            marca = request.form.get("marca", "")
            modelo = request.form.get("modelo", "")
            total = int(request.form.get("quantidade_total", 0))
            com_selo = int(request.form.get("quantidade_com_selo", 0))
            sem_selo = int(request.form.get("quantidade_sem_selo", 0))

            danos = []
            danos_qtd = request.form.getlist("dano_qtd[]")
            danos_desc = request.form.getlist("dano_desc[]")
            danos_obs = request.form.getlist("dano_obs[]")
            for i in range(len(danos_qtd)):
                if danos_qtd[i] and int(danos_qtd[i]) > 0:
                    danos.append({
                        "qtd": int(danos_qtd[i]),
                        "descricao": danos_desc[i],
                        "obs": danos_obs[i] if i < len(danos_obs) else ""
                    })

            salvar_contagem(
                ambiente_id=ambiente_id,
                material_id=material_id,
                marca=marca,
                modelo=modelo,
                qtd_total=total,
                qtd_com_selo=com_selo,
                qtd_sem_selo=sem_selo,
                usuario_id=session["user_id"],
                danos=danos
            )
            flash("Contagem salva com sucesso.", "success")
            return redirect(url_for("contagem.index", ambiente_id=ambiente_id))

        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"Erro ao salvar: {e}", "error")

    return render_template(
        "contagem_form.html", 
        ambiente=ambiente, 
        materiais=materiais,
        sugestoes=sugestoes,
        grupo=None,
        danos=[]
    )


@contagem_bp.route("/<ambiente_id>/editar/<grupo_id>", methods=["GET", "POST"])
@login_required
def editar(ambiente_id, grupo_id):
    ambiente = obter_ambiente(ambiente_id)
    if not ambiente or ambiente["status"] != "em_andamento":
        flash("Este ambiente não está em andamento.", "error")
        return redirect(url_for("ambientes.index"))

    grupo = obter_grupo(grupo_id)
    if not grupo or grupo["ambiente_id"] != ambiente_id:
        flash("Registro não encontrado neste ambiente.", "error")
        return redirect(url_for("contagem.index", ambiente_id=ambiente_id))

    materiais = [m for m in listar_materiais() if m["ativo"]]
    sugestoes = listar_marcas_modelos()
    danos_existentes = grupo.get("detalhes_danos", [])

    if request.method == "POST":
        if not validar_csrf(request.form.get("csrf_token")):
            flash("Sessão expirada.", "error")
            return redirect(url_for("contagem.editar", ambiente_id=ambiente_id, grupo_id=grupo_id))

        try:
            material_id = request.form.get("material_id")
            marca = request.form.get("marca", "")
            modelo = request.form.get("modelo", "")
            total = int(request.form.get("quantidade_total", 0))
            com_selo = int(request.form.get("quantidade_com_selo", 0))
            sem_selo = int(request.form.get("quantidade_sem_selo", 0))

            danos = []
            danos_qtd = request.form.getlist("dano_qtd[]")
            danos_desc = request.form.getlist("dano_desc[]")
            danos_obs = request.form.getlist("dano_obs[]")
            for i in range(len(danos_qtd)):
                if danos_qtd[i] and int(danos_qtd[i]) > 0:
                    danos.append({
                        "qtd": int(danos_qtd[i]),
                        "descricao": danos_desc[i],
                        "obs": danos_obs[i] if i < len(danos_obs) else ""
                    })

            salvar_contagem(
                ambiente_id=ambiente_id,
                material_id=material_id,
                marca=marca,
                modelo=modelo,
                qtd_total=total,
                qtd_com_selo=com_selo,
                qtd_sem_selo=sem_selo,
                usuario_id=session["user_id"],
                danos=danos,
                grupo_id=grupo_id
            )
            flash("Contagem atualizada com sucesso.", "success")
            return redirect(url_for("contagem.index", ambiente_id=ambiente_id))

        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "error")

    return render_template(
        "contagem_form.html", 
        ambiente=ambiente, 
        materiais=materiais,
        sugestoes=sugestoes,
        grupo=grupo,
        danos=danos_existentes
    )


@contagem_bp.route("/<ambiente_id>/excluir/<grupo_id>", methods=["POST"])
@login_required
def excluir(ambiente_id, grupo_id):
    if not validar_csrf(request.form.get("csrf_token")):
        flash("Sessão expirada.", "error")
        return redirect(url_for("contagem.index", ambiente_id=ambiente_id))

    ambiente = obter_ambiente(ambiente_id)
    if not ambiente or ambiente["status"] != "em_andamento":
        flash("Este ambiente não está em andamento.", "error")
        return redirect(url_for("ambientes.index"))

    grupo = obter_grupo(grupo_id)
    if not grupo or grupo["ambiente_id"] != ambiente_id:
        flash("Registro não encontrado neste ambiente.", "error")
        return redirect(url_for("contagem.index", ambiente_id=ambiente_id))

    try:
        excluir_grupo(grupo_id)
        flash("Material excluído com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "error")

    return redirect(url_for("contagem.index", ambiente_id=ambiente_id))