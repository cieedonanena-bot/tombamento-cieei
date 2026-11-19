"""
Rotas do dashboard.
"""
from flask import Blueprint, render_template

from services.auth_guard import login_required
from services.dashboard_service import obter_estatisticas

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    # Busca os dados reais do banco
    stats = obter_estatisticas()
    
    return render_template("dashboard.html", stats=stats)