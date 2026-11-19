"""
Serviço para calcular as estatísticas do Dashboard.
"""
from services.supabase_service import get_cliente_admin


def _cliente():
    return get_cliente_admin()


def obter_estatisticas() -> dict:
    """
    Consulta o banco e retorna todas as métricas do Dashboard.
    """
    cli = _cliente()

    # 1. Busca todos os grupos de contagem (para somar materiais e selos)
    grupos = cli.table("grupos_contagem").select(
        "quantidade_total, quantidade_com_selo, quantidade_sem_selo, tem_dano"
    ).execute().data or []

    total_materiais = sum(g["quantidade_total"] for g in grupos)
    total_com_selo = sum(g["quantidade_com_selo"] for g in grupos)
    total_sem_selo = sum(g["quantidade_sem_selo"] for g in grupos)
    grupos_com_dano = sum(1 for g in grupos if g["tem_dano"])

    # 2. Busca detalhes dos danos (para somar a quantidade exata de itens danificados)
    danos = cli.table("detalhes_danos").select("quantidade_danificada").execute().data or []
    total_itens_danificados = sum(d["quantidade_danificada"] for d in danos)

    # 3. Busca os ambientes (para contar os status)
    ambientes = cli.table("ambientes").select("status").execute().data or []
    total_ambientes = len(ambientes)
    ambientes_pendentes = sum(1 for a in ambientes if a["status"] == "pendente")
    ambientes_em_andamento = sum(1 for a in ambientes if a["status"] == "em_andamento")
    ambientes_concluidos = sum(1 for a in ambientes if a["status"] == "concluido")

    # 4. Calcula percentual de conclusão
    percentual = 0
    if total_ambientes > 0:
        percentual = round((ambientes_concluidos / total_ambientes) * 100, 1)

    # 5. Conta funcionários participantes (quem já assumiu alguma responsabilidade)
    responsabilidades = cli.table("responsabilidade_ambiente").select("funcionario_id").execute().data or []
    # Usa set() para garantir que não conta o mesmo funcionário duas vezes
    funcionarios_participantes = len(set(r["funcionario_id"] for r in responsabilidades))

    return {
        "total_materiais": total_materiais,
        "total_com_selo": total_com_selo,
        "total_sem_selo": total_sem_selo,
        "total_danificados": total_itens_danificados,
        "grupos_com_dano": grupos_com_dano,
        "total_ambientes": total_ambientes,
        "ambientes_pendentes": ambientes_pendentes,
        "ambientes_em_andamento": ambientes_em_andamento,
        "ambientes_concluidos": ambientes_concluidos,
        "percentual_conclusao": percentual,
        "funcionarios_participantes": funcionarios_participantes,
    }