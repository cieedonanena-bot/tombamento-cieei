"""
Serviço para consultar o histórico de ações.
"""
from services.supabase_service import get_cliente_admin


def _cliente():
    return get_cliente_admin()


def listar_historico(
    usuario_id: str | None = None,
    tabela: str | None = None,
    acao: str | None = None,
    limite: int = 100,
) -> list[dict]:
    """
    Retorna o histórico com filtros opcionais.
    """
    query = (
        _cliente()
        .table("historico")
        .select("id, tabela_afetada, registro_id, acao, usuario_id, justificativa, criado_em, dados_anteriores, dados_novos")
        .order("criado_em", desc=True)
        .limit(limite)
    )

    if usuario_id:
        query = query.eq("usuario_id", usuario_id)
    if tabela:
        query = query.eq("tabela_afetada", tabela)
    if acao:
        query = query.eq("acao", acao)

    registros = query.execute().data or []

    # Hidrata o nome dos usuários
    ids_usuarios = list({r["usuario_id"] for r in registros if r["usuario_id"]})
    if ids_usuarios:
        perfis = (
            _cliente()
            .table("perfis")
            .select("id, nome_completo")
            .in_("id", ids_usuarios)
            .execute()
            .data
            or []
        )
        nomes = {p["id"]: p["nome_completo"] for p in perfis}
        for r in registros:
            r["nome_usuario"] = nomes.get(r["usuario_id"], "Sistema")

    return registros