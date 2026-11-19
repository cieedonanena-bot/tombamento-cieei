"""
Regras de negócio para transferência de responsabilidade de ambientes.
"""
from datetime import datetime, timezone
from services.supabase_service import get_cliente_admin
from services.ambiente_service import obter_ambiente


def _cliente():
    return get_cliente_admin()


def _agora():
    return datetime.now(timezone.utc).isoformat()


def solicitar_transferencia(ambiente_id: str, solicitante_id: str, destinatario_id: str, motivo: str) -> dict:
    motivo = (motivo or "").strip()
    if len(motivo) < 10:
        raise ValueError("O motivo deve ter pelo menos 10 caracteres.")

    if solicitante_id == destinatario_id:
        raise ValueError("Não é possível transferir para si mesmo.")

    ambiente = obter_ambiente(ambiente_id)
    if not ambiente:
        raise ValueError("Ambiente não encontrado.")

    # Verifica se o destinatário existe e está ativo
    perfil = (
        _cliente().table("perfis").select("id, ativo, role, nome_completo")
        .eq("id", destinatario_id).single().execute().data
    )
    if not perfil:
        raise ValueError("Destinatário não encontrado.")
    if not perfil["ativo"]:
        raise ValueError(f"O funcionário '{perfil['nome_completo']}' está inativo.")

    # Cria a solicitação
    resp = _cliente().table("solicitacoes_transferencia").insert({
        "ambiente_id": ambiente_id,
        "solicitante_id": solicitante_id,
        "destinatario_id": destinatario_id,
        "motivo": motivo,
    }).execute()

    return resp.data[0] if resp.data else {}


def listar_pendentes() -> list[dict]:
    """Lista solicitações pendentes para o admin."""
    registros = (
        _cliente().table("solicitacoes_transferencia")
        .select("*")
        .eq("status", "pendente")
        .order("criado_em", desc=True)
        .execute().data or []
    )

    if not registros:
        return []

    # Hidrata dados
    ids_perfis = set()
    ids_ambientes = set()
    for r in registros:
        ids_perfis.add(r["solicitante_id"])
        ids_perfis.add(r["destinatario_id"])
        ids_ambientes.add(r["ambiente_id"])

    perfis = (
        _cliente().table("perfis").select("id, nome_completo")
        .in_("id", list(ids_perfis)).execute().data or []
    )
    ambientes = (
        _cliente().table("ambientes").select("id, nome")
        .in_("id", list(ids_ambientes)).execute().data or []
    )
    nomes = {p["id"]: p["nome_completo"] for p in perfis}
    nomes_amb = {a["id"]: a["nome"] for a in ambientes}

    for r in registros:
        r["nome_solicitante"] = nomes.get(r["solicitante_id"], "?")
        r["nome_destinatario"] = nomes.get(r["destinatario_id"], "?")
        r["nome_ambiente"] = nomes_amb.get(r["ambiente_id"], "?")

    return registros


def aprovar_transferencia(solicitacao_id: str, admin_id: str) -> dict:
    """Aprova a transferência: muda o responsável do ambiente."""
    sol = _obter_solicitacao(solicitacao_id)
    if not sol or sol["status"] != "pendente":
        raise ValueError("Solicitação não encontrada ou já resolvida.")

    cli = _cliente()

    # Encerra responsabilidade antiga
    cli.table("responsabilidade_ambiente").update({
        "ativo": False,
        "finalizado_em": _agora()
    }).eq("ambiente_id", sol["ambiente_id"]).eq("ativo", True).execute()

    # Cria a nova
    cli.table("responsabilidade_ambiente").insert({
        "ambiente_id": sol["ambiente_id"],
        "funcionario_id": sol["destinatario_id"],
        "ativo": True,
    }).execute()

    # Atualiza a solicitação
    cli.table("solicitacoes_transferencia").update({
        "status": "aprovada",
        "aprovador_id": admin_id,
        "resolvido_em": _agora(),
    }).eq("id", solicitacao_id).execute()

    return {"ok": True}


def rejeitar_transferencia(solicitacao_id: str, admin_id: str, justificativa: str) -> dict:
    if not justificativa or len(justificativa.strip()) < 5:
        raise ValueError("Justificativa obrigatória (mín. 5 caracteres).")

    _cliente().table("solicitacoes_transferencia").update({
        "status": "rejeitada",
        "aprovador_id": admin_id,
        "justificativa_aprovacao": justificativa.strip(),
        "resolvido_em": _agora(),
    }).eq("id", solicitacao_id).execute()

    return {"ok": True}


def _obter_solicitacao(sol_id: str) -> dict | None:
    resp = (
        _cliente().table("solicitacoes_transferencia").select("*")
        .eq("id", sol_id).single().execute()
    )
    return resp.data if resp.data else None