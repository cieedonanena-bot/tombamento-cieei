"""
Regras de negócio da contagem de materiais.
"""
from datetime import datetime, timezone
from services.supabase_service import get_cliente_admin


def _cliente():
    return get_cliente_admin()


def _agora():
    return datetime.now(timezone.utc).isoformat()


def _normalizar(texto: str | None) -> str:
    return (texto or "").strip()


def listar_grupos_por_ambiente(ambiente_id: str) -> list[dict]:
    resp = (
        _cliente()
        .table("grupos_contagem")
        .select("*, materiais(nome)")
        .eq("ambiente_id", ambiente_id)
        .order("criado_em")
        .execute()
    )
    return resp.data or []


def salvar_contagem(
    ambiente_id: str, material_id: str, marca: str, modelo: str,
    qtd_total: int, qtd_com_selo: int, qtd_sem_selo: int,
    usuario_id: str, danos: list[dict] | None = None,
) -> dict:
    
    if qtd_total != (qtd_com_selo + qtd_sem_selo):
        raise ValueError("A soma de 'Com Selo' e 'Sem Selo' deve ser igual à Quantidade Total.")

    if qtd_total < 0 or qtd_com_selo < 0 or qtd_sem_selo < 0:
        raise ValueError("As quantidades não podem ser negativas.")

    marca = _normalizar(marca) or "Não identificado"
    modelo = _normalizar(modelo) or "Não identificado"

    existente = (
        _cliente().table("grupos_contagem").select("id")
        .eq("ambiente_id", ambiente_id).eq("material_id", material_id)
        .eq("marca", marca).eq("modelo", modelo).execute()
    )

    dados = {
        "ambiente_id": ambiente_id, "material_id": material_id,
        "marca": marca, "modelo": modelo,
        "quantidade_total": qtd_total,
        "quantidade_com_selo": qtd_com_selo,
        "quantidade_sem_selo": qtd_sem_selo,
        "atualizado_por": usuario_id, "atualizado_em": _agora(),
    }

    if existente.data:
        grupo_id = existente.data[0]["id"]
        _cliente().table("grupos_contagem").update(dados).eq("id", grupo_id).execute()
    else:
        dados["criado_por"] = usuario_id
        dados["criado_em"] = _agora()
        resp = _cliente().table("grupos_contagem").insert(dados).execute()
        grupo_id = resp.data[0]["id"]

    _cliente().table("detalhes_danos").delete().eq("grupo_id", grupo_id).execute()
    
    if danos:
        for d in danos:
            if d.get("qtd", 0) > 0 and d.get("descricao"):
                _cliente().table("detalhes_danos").insert({
                    "grupo_id": grupo_id,
                    "quantidade_danificada": d["qtd"],
                    "descricao": d["descricao"],
                    "observacao": d.get("obs", "")
                }).execute()
        _cliente().table("grupos_contagem").update({"tem_dano": True}).eq("id", grupo_id).execute()
    else:
        _cliente().table("grupos_contagem").update({"tem_dano": False}).eq("id", grupo_id).execute()

    return {"id": grupo_id}


def listar_marcas_modelos() -> dict:
    """
    Retorna todas as marcas e modelos distintos já cadastrados.
    Usado para preencher autocomplete no formulário de contagem.
    """
    try:
        resp = (
            _cliente()
            .table("grupos_contagem")
            .select("marca, modelo")
            .execute()
        )
        dados = resp.data or []
        
        # Filtra "Não identificado" para não poluir a lista
        marcas = sorted({
            d["marca"] for d in dados 
            if d.get("marca") and d["marca"] != "Não identificado"
        })
        modelos = sorted({
            d["modelo"] for d in dados 
            if d.get("modelo") and d["modelo"] != "Não identificado"
        })
        
        return {"marcas": marcas, "modelos": modelos}
    except Exception:
        return {"marcas": [], "modelos": []}