"""
Serviço de agregação de dados para os relatórios.
"""
from datetime import datetime, timezone
from services.supabase_service import get_cliente_admin


def _cliente():
    return get_cliente_admin()


def _data_emissao() -> str:
    return datetime.now(timezone.utc).strftime("%d/%m/%Y às %H:%M")


# ====================================================================
# RELATÓRIO 1 — OFICIAL DE TOMBAMENTO (sem localização)
# ====================================================================
def dados_relatorio_oficial() -> dict:
    """
    Agrupa por (material + marca + modelo), somando de TODOS os ambientes.
    """
    grupos = (
        _cliente()
        .table("grupos_contagem")
        .select("quantidade_total, quantidade_com_selo, quantidade_sem_selo, marca, modelo, materiais(nome)")
        .execute()
        .data
        or []
    )

    agregado = {}
    for g in grupos:
        nome_mat = g["materiais"]["nome"] if g.get("materiais") else "?"
        chave = (nome_mat, g["marca"], g["modelo"])
        if chave not in agregado:
            agregado[chave] = {
                "material": nome_mat,
                "marca": g["marca"],
                "modelo": g["modelo"],
                "total": 0,
                "com_selo": 0,
                "sem_selo": 0,
            }
        agregado[chave]["total"] += g["quantidade_total"]
        agregado[chave]["com_selo"] += g["quantidade_com_selo"]
        agregado[chave]["sem_selo"] += g["quantidade_sem_selo"]

    linhas = sorted(agregado.values(), key=lambda x: (x["material"], x["marca"], x["modelo"]))

    total_geral = sum(l["total"] for l in linhas)
    total_com_selo = sum(l["com_selo"] for l in linhas)
    total_sem_selo = sum(l["sem_selo"] for l in linhas)

    return {
        "data_emissao": _data_emissao(),
        "linhas": linhas,
        "total_geral": total_geral,
        "total_com_selo": total_com_selo,
        "total_sem_selo": total_sem_selo,
        "necessidade_selos": total_sem_selo,  # Cada item sem selo precisa de um
    }


# ====================================================================
# RELATÓRIO 2 — DETALHADO INTERNO (por ambiente)
# ====================================================================
def dados_relatorio_detalhado() -> dict:
    """
    Organizado por ambiente, com responsável, danos e subtotais.
    """
    cli = _cliente()

    ambientes = (
        cli.table("ambientes")
        .select("id, nome, bloco_setor, status")
        .order("nome")
        .execute()
        .data
        or []
    )

    grupos = (
        cli.table("grupos_contagem")
        .select("id, ambiente_id, marca, modelo, quantidade_total, quantidade_com_selo, quantidade_sem_selo, tem_dano, materiais(nome), criado_em, detalhes_danos(quantidade_danificada, descricao, observacao)")
        .execute()
        .data
        or []
    )

    # Responsáveis ativos
    responsabilidades = (
        cli.table("responsabilidade_ambiente")
        .select("ambiente_id, iniciado_em, perfis!funcionario_id(nome_completo)")
        .eq("ativo", True)
        .execute()
        .data
        or []
    )
    responsavel_por_ambiente = {}
    for r in responsabilidades:
        nome = r.get("perfis", {}).get("nome_completo", "?") if r.get("perfis") else "?"
        responsavel_por_ambiente[r["ambiente_id"]] = {
            "nome": nome,
            "iniciado_em": r["iniciado_em"],
        }

    por_ambiente = {}
    for g in grupos:
        amb_id = g["ambiente_id"]
        if amb_id not in por_ambiente:
            por_ambiente[amb_id] = []
        danos = g.get("detalhes_danos") or []
        danos_txt = " ; ".join(f"{d['quantidade_danificada']}x {d['descricao']}" for d in danos) if danos else ""
        por_ambiente[amb_id].append({
            "material": g["materiais"]["nome"] if g.get("materiais") else "?",
            "marca": g["marca"],
            "modelo": g["modelo"],
            "total": g["quantidade_total"],
            "com_selo": g["quantidade_com_selo"],
            "sem_selo": g["quantidade_sem_selo"],
            "qtd_danificada": sum(d["quantidade_danificada"] for d in danos),
            "descricao_danos": danos_txt,
            "criado_em": g["criado_em"],
        })

    ambientes_com_dados = []
    for a in ambientes:
        itens = por_ambiente.get(a["id"], [])
        if not itens:
            continue
        subtotal = {
            "total": sum(i["total"] for i in itens),
            "com_selo": sum(i["com_selo"] for i in itens),
            "sem_selo": sum(i["sem_selo"] for i in itens),
            "qtd_danificada": sum(i["qtd_danificada"] for i in itens),
        }
        resp = responsavel_por_ambiente.get(a["id"], {})
        ambientes_com_dados.append({
            "ambiente": a["nome"],
            "bloco_setor": a["bloco_setor"] or "—",
            "status": a["status"],
            "responsavel": resp.get("nome", "—"),
            "itens": sorted(itens, key=lambda x: (x["material"], x["marca"], x["modelo"])),
            "subtotal": subtotal,
        })

    # Totais gerais
    total_geral = sum(a["subtotal"]["total"] for a in ambientes_com_dados)
    total_com_selo = sum(a["subtotal"]["com_selo"] for a in ambientes_com_dados)
    total_sem_selo = sum(a["subtotal"]["sem_selo"] for a in ambientes_com_dados)
    total_danificados = sum(a["subtotal"]["qtd_danificada"] for a in ambientes_com_dados)

    # Por material (para aba extra)
    por_material = {}
    for a in ambientes_com_dados:
        for i in a["itens"]:
            k = i["material"]
            if k not in por_material:
                por_material[k] = {"material": k, "total": 0, "com_selo": 0, "sem_selo": 0}
            por_material[k]["total"] += i["total"]
            por_material[k]["com_selo"] += i["com_selo"]
            por_material[k]["sem_selo"] += i["sem_selo"]

    # Por marca/modelo
    por_marca_modelo = {}
    for a in ambientes_com_dados:
        for i in a["itens"]:
            k = (i["material"], i["marca"], i["modelo"])
            if k not in por_marca_modelo:
                por_marca_modelo[k] = {
                    "material": i["material"],
                    "marca": i["marca"],
                    "modelo": i["modelo"],
                    "total": 0, "com_selo": 0, "sem_selo": 0,
                }
            por_marca_modelo[k]["total"] += i["total"]
            por_marca_modelo[k]["com_selo"] += i["com_selo"]
            por_marca_modelo[k]["sem_selo"] += i["sem_selo"]

    return {
        "data_emissao": _data_emissao(),
        "ambientes": ambientes_com_dados,
        "por_material": sorted(por_material.values(), key=lambda x: x["material"]),
        "por_marca_modelo": sorted(por_marca_modelo.values(), key=lambda x: (x["material"], x["marca"])),
        "total_geral": total_geral,
        "total_com_selo": total_com_selo,
        "total_sem_selo": total_sem_selo,
        "total_danificados": total_danificados,
        "necessidade_selos": total_sem_selo,
        "total_ambientes_conferidos": len(ambientes_com_dados),
    }


# ====================================================================
# RELATÓRIO 3 — MATERIAIS DANIFICADOS
# ====================================================================
def dados_relatorio_danos() -> dict:
    """
    Apenas grupos com danos declarados, com detalhes completos.
    """
    cli = _cliente()

    grupos = (
        cli.table("grupos_contagem")
        .select("id, ambiente_id, marca, modelo, quantidade_total, quantidade_com_selo, quantidade_sem_selo, materiais(nome), ambientes(nome, bloco_setor), detalhes_danos(quantidade_danificada, descricao, observacao)")
        .eq("tem_dano", True)
        .execute()
        .data
        or []
    )

    # Responsáveis
    responsabilidades = (
        cli.table("responsabilidade_ambiente")
        .select("ambiente_id, perfis!funcionario_id(nome_completo)")
        .eq("ativo", True)
        .execute()
        .data
        or []
    )
    resp_por_amb = {}
    for r in responsabilidades:
        nome = r.get("perfis", {}).get("nome_completo", "?") if r.get("perfis") else "?"
        resp_por_amb[r["ambiente_id"]] = nome

    linhas = []
    for g in grupos:
        danos = g.get("detalhes_danos") or []
        ambiente_nome = g.get("ambientes", {}).get("nome", "?") if g.get("ambientes") else "?"
        ambiente_bloco = g.get("ambientes", {}).get("bloco_setor", "") if g.get("ambientes") else ""
        material_nome = g.get("materiais", {}).get("nome", "?") if g.get("materiais") else "?"

        for d in danos:
            linhas.append({
                "material": material_nome,
                "marca": g["marca"],
                "modelo": g["modelo"],
                "ambiente": ambiente_nome,
                "bloco_setor": ambiente_bloco or "—",
                "qtd_danificada": d["quantidade_danificada"],
                "descricao": d["descricao"],
                "observacao": d.get("observacao") or "—",
                "com_selo": g["quantidade_com_selo"],
                "sem_selo": g["quantidade_sem_selo"],
                "total": g["quantidade_total"],
                "responsavel": resp_por_amb.get(g["ambiente_id"], "—"),
            })

    linhas.sort(key=lambda x: (x["ambiente"], x["material"], x["marca"]))

    # Agregações para resumo
    total_itens_danificados = sum(l["qtd_danificada"] for l in linhas)
    por_ambiente = {}
    for l in linhas:
        k = l["ambiente"]
        if k not in por_ambiente:
            por_ambiente[k] = {"ambiente": k, "qtd": 0, "ocorrencias": 0}
        por_ambiente[k]["qtd"] += l["qtd_danificada"]
        por_ambiente[k]["ocorrencias"] += 1

    por_tipo = {}
    for l in linhas:
        k = l["material"]
        if k not in por_tipo:
            por_tipo[k] = {"material": k, "qtd": 0, "ocorrencias": 0}
        por_tipo[k]["qtd"] += l["qtd_danificada"]
        por_tipo[k]["ocorrencias"] += 1

    return {
        "data_emissao": _data_emissao(),
        "linhas": linhas,
        "total_itens_danificados": total_itens_danificados,
        "total_ocorrencias": len(linhas),
        "por_ambiente": sorted(por_ambiente.values(), key=lambda x: -x["qtd"]),
        "por_tipo": sorted(por_tipo.values(), key=lambda x: -x["qtd"]),
    }