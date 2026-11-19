"""
Ponto de entrada da aplicação Flask.
"""
import os  # <-- ADICIONADO PARA PRODUÇÃO
from flask import Flask, jsonify, session, redirect, url_for

from config import Config
from services.supabase_service import init_supabase, get_cliente_admin
from services.auth_guard import get_csrf_token
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.ambientes import ambientes_bp
from routes.materiais import materiais_bp
from routes.contagem import contagem_bp
from routes.funcionarios import funcionarios_bp
from routes.administracao import administracao_bp
from routes.relatorios import relatorios_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Desativa o cache de arquivos estáticos (CSS/JS) em desenvolvimento
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    Config.validar()
    init_supabase()

    # Registrando todos os blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ambientes_bp)
    app.register_blueprint(materiais_bp)
    app.register_blueprint(contagem_bp)
    app.register_blueprint(funcionarios_bp)
    app.register_blueprint(administracao_bp)
    app.register_blueprint(relatorios_bp)

    @app.context_processor
    def inject_csrf():
        return {"csrf_token": get_csrf_token()}

    @app.route("/")
    def raiz():
        if session.get("user_id"):
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    @app.route("/health")
    def health():
        try:
            cliente = get_cliente_admin()
            cliente.table("ambientes").select("id", count="exact").limit(1).execute()
            return jsonify({"app": "OK", "supabase": "OK"}), 200
        except Exception as e:
            return jsonify({"app": "OK", "supabase": "ERRO", "detalhe": str(e)}), 500

    return app


app = create_app()


if __name__ == "__main__":
    # O Render define a variável de ambiente PORT automaticamente.
    # Localmente, usa a porta 5000 como fallback.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)