"""
Rotas para geração dos 3 relatórios em PDF e Excel.
"""
from flask import Blueprint, render_template, send_file, flash, redirect, url_for

from services.auth_guard import login_required
from services.relatorio_service import (
    dados_relatorio_oficial, dados_relatorio_detalhado, dados_relatorio_danos,
)
from services.relatorio_pdf import (
    gerar_pdf_oficial, gerar_pdf_detalhado, gerar_pdf_danos,
)
from services.relatorio_excel import (
    gerar_excel_oficial, gerar_excel_detalhado, gerar_excel_danos,
)

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/")
@login_required
def index():
    return render_template("relatorios.html")


# ============ PDF ============
@relatorios_bp.route("/oficial.pdf")
@login_required
def oficial_pdf():
    try:
        buf = gerar_pdf_oficial(dados_relatorio_oficial())
        return send_file(
            buf, mimetype="application/pdf",
            as_attachment=True,
            download_name="relatorio_oficial_tombamento.pdf",
        )
    except Exception as e:
        flash(f"Erro ao gerar PDF: {e}", "error")
        return redirect(url_for("relatorios.index"))


@relatorios_bp.route("/detalhado.pdf")
@login_required
def detalhado_pdf():
    try:
        buf = gerar_pdf_detalhado(dados_relatorio_detalhado())
        return send_file(
            buf, mimetype="application/pdf",
            as_attachment=True,
            download_name="relatorio_detalhado_interno.pdf",
        )
    except Exception as e:
        flash(f"Erro ao gerar PDF: {e}", "error")
        return redirect(url_for("relatorios.index"))


@relatorios_bp.route("/danos.pdf")
@login_required
def danos_pdf():
    try:
        buf = gerar_pdf_danos(dados_relatorio_danos())
        return send_file(
            buf, mimetype="application/pdf",
            as_attachment=True,
            download_name="relatorio_materiais_danificados.pdf",
        )
    except Exception as e:
        flash(f"Erro ao gerar PDF: {e}", "error")
        return redirect(url_for("relatorios.index"))


# ============ EXCEL ============
@relatorios_bp.route("/oficial.xlsx")
@login_required
def oficial_excel():
    try:
        buf = gerar_excel_oficial(dados_relatorio_oficial())
        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="relatorio_oficial_tombamento.xlsx",
        )
    except Exception as e:
        flash(f"Erro ao gerar Excel: {e}", "error")
        return redirect(url_for("relatorios.index"))


@relatorios_bp.route("/detalhado.xlsx")
@login_required
def detalhado_excel():
    try:
        buf = gerar_excel_detalhado(dados_relatorio_detalhado())
        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="relatorio_detalhado_interno.xlsx",
        )
    except Exception as e:
        flash(f"Erro ao gerar Excel: {e}", "error")
        return redirect(url_for("relatorios.index"))


@relatorios_bp.route("/danos.xlsx")
@login_required
def danos_excel():
    try:
        buf = gerar_excel_danos(dados_relatorio_danos())
        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="relatorio_materiais_danificados.xlsx",
        )
    except Exception as e:
        flash(f"Erro ao gerar Excel: {e}", "error")
        return redirect(url_for("relatorios.index"))