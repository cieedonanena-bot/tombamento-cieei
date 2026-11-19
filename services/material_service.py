"""
Regras de negócio do catálogo de materiais.
"""
from services.supabase_service import get_cliente_admin


def _cliente():
    return get_cliente_admin()


def _normalizar(texto: str | None) -> str:
    return (texto or "").strip()


def listar_materiais(incluir_inativos: bool = True) -> list[dict]:
    """
    Lista materiais ordenados por nome.
    Por padrão inclui inativos para a administradora ver todos.
    """
    query = _cliente().table("materiais").select(
        "id, nome, ativo, criado_em"
    ).order("nome")

    if not incluir_inativos:
        query = query.eq("ativo", True)

    return query.execute().data or []


def obter_material(material_id: str) -> dict | None:
    resp = (
        _cliente()
        .table("materiais")
        .select("*")
        .eq("id", material_id)
        .single()
        .execute()
    )
    return resp.data if resp.data else None


def _contar_uso(material_id: str) -> int:
    """Quantos grupos de contagem já usam este material."""
    resp = (
        _cliente()
        .table("grupos_contagem")
        .select("id", count="exact")
        .eq("material_id", material_id)
        .execute()
    )
    return resp.count or 0


def criar_material(nome: str) -> dict:
    """
    Cria material novo. Levanta ValueError em caso de duplicidade
    (considerando acentos, maiúsculas e espaços extras).
    """
    nome = _normalizar(nome)
    if not nome:
        raise ValueError("O nome do material é obrigatório.")
    if len(nome) < 2:
        raise ValueError("O nome do material deve ter pelo menos 2 caracteres.")

    try:
        resp = _cliente().table("materiais").insert({"nome": nome}).execute()
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            raise ValueError(
                f"Já existe um material com o nome '{nome}' "
                f"(considerando acentos e maiúsculas)."
            )
        raise

    return resp.data[0] if resp.data else {}


def editar_material(material_id: str, nome: str) -> dict:
    nome = _normalizar(nome)
    if not nome:
        raise ValueError("O nome do material é obrigatório.")
    if len(nome) < 2:
        raise ValueError("O nome do material deve ter pelo menos 2 caracteres.")

    try:
        resp = (
            _cliente()
            .table("materiais")
            .update({"nome": nome})
            .eq("id", material_id)
            .execute()
        )
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            raise ValueError(f"Já existe um material com o nome '{nome}'.")
        raise

    return resp.data[0] if resp.data else {}


def alternar_ativo(material_id: str) -> dict:
    """
    Ativa / desativa um material (soft delete).
    Não permite desativar se houver contagens vinculadas — o registro
    é histórico e deve permanecer consultável.
    """
    material = obter_material(material_id)
    if not material:
        raise ValueError("Material não encontrado.")

    if material["ativo"]:
        usos = _contar_uso(material_id)
        if usos > 0:
            raise ValueError(
                f"Este material está em uso em {usos} registro(s) de contagem "
                f"e não pode ser desativado. Renomeie-o, se necessário."
            )

    novo_estado = not material["ativo"]
    _cliente().table("materiais").update(
        {"ativo": novo_estado}
    ).eq("id", material_id).execute()

    return {"ativo": novo_estado}