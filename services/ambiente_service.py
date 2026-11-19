"""
Regras de negócio dos ambientes.
Toda a validação de permissão é feita aqui (defense in depth).
"""
from datetime import datetime, timezone
from supabase import create_client

from config import Config
from services.supabase_service import get_cliente_admin


def _cliente():
    return get_cliente_admin()


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalizar(texto: str | None) -> str:
    return (texto or "").strip()


# ==================== LEITURA ====================
def listar_ambientes() -> list[dict]:
    """
    Retorna todos os ambientes ordenados por nome, com o responsável
    ativo (se houver) já resolvido em cada item.
    """
    cli = _cliente()

    ambientes = (
        cli.table("ambientes")
        .select("id, nome, bloco_setor, observacao, status, criado_em, atualizado_em")
        .order("nome")
        .execute()
        .data
        or []
    )

    responsabilidades = (
        cli.table("responsabilidade_ambiente")
        .select("id, ambiente_id, funcionario_id, iniciado_em, ativo")
        .eq("ativo", True)
        .execute()
        .data
        or []
    )

    if responsabilidades:
        ids_funcionarios = [r["funcionario_id"] for r in responsabilidades]
        perfis = (
            cli.table("perfis")
            .select("id, nome_completo")
            .in_("id", ids_funcionarios)
            .execute()
            .data
            or []
        )
        nomes = {p["id"]: p["nome_completo"] for p in perfis}
        resp_por_ambiente = {
            r["ambiente_id"]: {
                **r,
                "nome_responsavel": nomes.get(r["funcionario_id"], "Desconhecido"),
            }
            for r in responsabilidades
        }
    else:
        resp_por_ambiente = {}

    for amb in ambientes:
        amb["responsavel"] = resp_por_ambiente.get(amb["id"])

    return ambientes


def obter_ambiente(ambiente_id: str) -> dict | None:
    resp = (
        _cliente()
        .table("ambientes")
        .select("*")
        .eq("id", ambiente_id)
        .single()
        .execute()
    )
    return resp.data if resp.data else None


# ==================== CRIAÇÃO ====================
def criar_ambiente(nome: str, bloco_setor: str, observacao: str) -> dict:
    """
    Cria um ambiente novo. Levanta ValueError em caso de duplicidade.
    """
    nome = _normalizar(nome)
    if not nome:
        raise ValueError("O nome do ambiente é obrigatório.")

    dados = {
        "nome": nome,
        "bloco_setor": _normalizar(bloco_setor) or None,
        "observacao": _normalizar(observacao) or None,
        "status": "pendente",
    }

    try:
        resp = _cliente().table("ambientes").insert(dados).execute()
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            raise ValueError(
                f"Já existe um ambiente com o nome '{nome}' "
                f"(considerando acentos e maiúsculas)."
            )
        raise

    return resp.data[0] if resp.data else {}


# ==================== EDIÇÃO ====================
def editar_ambiente(
    ambiente_id: str, nome: str, bloco_setor: str, observacao: str
) -> dict:
    nome = _normalizar(nome)
    if not nome:
        raise ValueError("O nome do ambiente é obrigatório.")

    dados = {
        "nome": nome,
        "bloco_setor": _normalizar(bloco_setor) or None,
        "observacao": _normalizar(observacao) or None,
    }

    try:
        resp = (
            _cliente()
            .table("ambientes")
            .update(dados)
            .eq("id", ambiente_id)
            .execute()
        )
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            raise ValueError(f"Já existe um ambiente com o nome '{nome}'.")
        raise

    return resp.data[0] if resp.data else {}


# ==================== RESPONSABILIDADE ====================
def iniciar_responsabilidade(ambiente_id: str, funcionario_id: str) -> dict:
    """
    Assume responsabilidade por um ambiente.
    Bloqueia se já houver outro responsável ativo.
    """
    cli = _cliente()

    # 1. Ambiente existe?
    amb = obter_ambiente(ambiente_id)
    if not amb:
        raise ValueError("Ambiente não encontrado.")

    if amb["status"] == "concluido":
        raise ValueError("Este ambiente já foi concluído. Solicite reabertura ao administrador.")

    # 2. Já tem responsável ativo?
    existentes = (
        cli.table("responsabilidade_ambiente")
        .select("funcionario_id, iniciado_em, perfis!funcionario_id(nome_completo)")
        .eq("ambiente_id", ambiente_id)
        .eq("ativo", True)
        .execute()
        .data
        or []
    )

    if existentes:
        r = existentes[0]
        if r["funcionario_id"] == funcionario_id:
            # Já é o próprio — idempotente
            return {"ja_era_responsavel": True}
        nome = "outro funcionário"
        if isinstance(r.get("perfis"), dict):
            nome = r["perfis"].get("nome_completo", nome)
        raise ValueError(
            f"ESTE AMBIENTE JÁ ESTÁ EM PROCESSO DE CONFERÊNCIA.\n"
            f"Responsável: {nome}\n"
            f"Início: {r['iniciado_em']}"
        )

    # 3. Cria responsabilidade + muda status do ambiente
    try:
        cli.table("responsabilidade_ambiente").insert({
            "ambiente_id": ambiente_id,
            "funcionario_id": funcionario_id,
            "ativo": True,
        }).execute()

        cli.table("ambientes").update({"status": "em_andamento"}).eq(
            "id", ambiente_id
        ).execute()

        _registrar_historico(
            tabela="ambientes",
            registro_id=ambiente_id,
            acao="INICIAR_CONFERENCIA",
            dados_novos={"funcionario_id": funcionario_id, "status": "em_andamento"},
            usuario_id=funcionario_id,
        )

        return {"ok": True}
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            raise ValueError(
                "ESTE AMBIENTE JÁ ESTÁ EM PROCESSO DE CONFERÊNCIA."
            )
        raise


def finalizar_responsabilidade(ambiente_id: str, funcionario_id: str) -> dict:
    """
    Finaliza a conferência de um ambiente. Somente o responsável ativo
    ou admin podem finalizar.
    """
    cli = _cliente()

    ativos = (
        cli.table("responsabilidade_ambiente")
        .select("id, funcionario_id")
        .eq("ambiente_id", ambiente_id)
        .eq("ativo", True)
        .execute()
        .data
        or []
    )

    if not ativos:
        raise ValueError("Nenhum responsável ativo para este ambiente.")

    responsavel = ativos[0]
    if responsavel["funcionario_id"] != funcionario_id:
        raise ValueError("Apenas o responsável atual pode finalizar este ambiente.")

    agora = _agora_iso()
    cli.table("responsabilidade_ambiente").update({
        "ativo": False,
        "finalizado_em": agora,
    }).eq("id", responsavel["id"]).execute()

    cli.table("ambientes").update({"status": "concluido"}).eq(
        "id", ambiente_id
    ).execute()

    _registrar_historico(
        tabela="ambientes",
        registro_id=ambiente_id,
        acao="FINALIZAR_CONFERENCIA",
        dados_novos={"funcionario_id": funcionario_id, "status": "concluido"},
        usuario_id=funcionario_id,
    )

    return {"ok": True}


def reabrir_ambiente(
    ambiente_id: str, admin_id: str, justificativa: str
) -> dict:
    """
    Admin reabre um ambiente concluído, com justificativa obrigatória.
    """
    if not justificativa or len(justificativa.strip()) < 10:
        raise ValueError("A justificativa deve ter pelo menos 10 caracteres.")

    amb = obter_ambiente(ambiente_id)
    if not amb:
        raise ValueError("Ambiente não encontrado.")
    if amb["status"] != "concluido":
        raise ValueError("Somente ambientes concluídos podem ser reabertos.")

    _cliente().table("ambientes").update({"status": "pendente"}).eq(
        "id", ambiente_id
    ).execute()

    _registrar_historico(
        tabela="ambientes",
        registro_id=ambiente_id,
        acao="REABRIR_AMBIENTE",
        dados_anteriores={"status": "concluido"},
        dados_novos={"status": "pendente"},
        usuario_id=admin_id,
        justificativa=justificativa.strip(),
    )

    return {"ok": True}


# ==================== HISTÓRICO ====================
def _registrar_historico(
    tabela: str,
    registro_id: str,
    acao: str,
    usuario_id: str,
    dados_novos: dict | None = None,
    dados_anteriores: dict | None = None,
    justificativa: str | None = None,
):
    try:
        _cliente().table("historico").insert({
            "tabela_afetada": tabela,
            "registro_id": registro_id,
            "acao": acao,
            "dados_anteriores": dados_anteriores,
            "dados_novos": dados_novos,
            "usuario_id": usuario_id,
            "justificativa": justificativa,
        }).execute()
    except Exception:
        # Histórico nunca deve quebrar a operação principal
        pass