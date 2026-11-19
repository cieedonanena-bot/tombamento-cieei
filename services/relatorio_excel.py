"""
Geração de relatórios em Excel com OpenPyXL.
"""
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


AZUL = "FF173C70"
AZUL_CLARO = "FFDBEAFE"
CINZA_CLARO = "FFF3F6FA"
VERDE = "FF16A34A"
VERMELHO = "FFDC2626"

BORDA = Border(
    left=Side(style="thin", color="FFE2E8F0"),
    right=Side(style="thin", color="FFE2E8F0"),
    top=Side(style="thin", color="FFE2E8F0"),
    bottom=Side(style="thin", color="FFE2E8F0"),
)


def _cabecalho_aba(ws, titulo: str):
    """Escreve o cabeçalho institucional no topo da aba."""
    ws.merge_cells("A1:H1")
    ws["A1"] = "CENTRO INTEGRADO DE EDUCAÇÃO ESPECIAL E ENSINO INFANTIL DONA NENA – CIEEI"
    ws["A1"].font = Font(bold=True, size=11, color="FFFFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=AZUL)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 24

    ws.merge_cells("A2:H2")
    ws["A2"] = titulo
    ws["A2"].font = Font(bold=True, size=13, color=AZUL)
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    ws.merge_cells("A3:H3")
    ws["A3"] = "TOMBAMENTO CIEEI DONA NENA"
    ws["A3"].font = Font(italic=True, size=10, color="FF64748B")
    ws["A3"].alignment = Alignment(horizontal="center")


def _cabecalho_tabela(ws, linha: int, colunas: list):
    for col, nome in enumerate(colunas, start=1):
        cell = ws.cell(row=linha, column=col, value=nome)
        cell.font = Font(bold=True, color="FFFFFFFF", size=10)
        cell.fill = PatternFill("solid", fgColor=AZUL)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDA
    ws.row_dimensions[linha].height = 28


def _ajustar_colunas(ws, larguras: list):
    for i, w in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _linhas_tabela(ws, inicio: int, linhas: list):
    for idx, linha in enumerate(linhas):
        for col, valor in enumerate(linha, start=1):
            cell = ws.cell(row=inicio + idx, column=col, value=valor)
            cell.border = BORDA
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if idx % 2 == 1:
                cell.fill = PatternFill("solid", fgColor=CINZA_CLARO)
    return inicio + len(linhas)


# ====================================================================
# EXCEL 1 — OFICIAL
# ====================================================================
def gerar_excel_oficial(dados: dict) -> BytesIO:
    wb = Workbook()

    # --- Aba 1: RESUMO GERAL ---
    ws = wb.active
    ws.title = "RESUMO GERAL"
    _cabecalho_aba(ws, "RELATÓRIO GERAL DE LEVANTAMENTO PATRIMONIAL")

    resumo = [
        ["Data de emissão", dados["data_emissao"]],
        ["Total geral de itens", dados["total_geral"]],
        ["Itens com selo", dados["total_com_selo"]],
        ["Itens sem selo", dados["total_sem_selo"]],
        ["Necessidade de selos", dados["necessidade_selos"]],
    ]
    linha = 5
    for label, valor in resumo:
        ws.cell(row=linha, column=1, value=label).font = Font(bold=True, color=AZUL)
        ws.cell(row=linha, column=2, value=valor)
        linha += 1
    _ajustar_colunas(ws, [30, 20])

    # --- Aba 2: MATERIAIS ---
    ws2 = wb.create_sheet("MATERIAIS")
    _cabecalho_aba(ws2, "Materiais Agrupados")
    _cabecalho_tabela(ws2, 5, ["Material", "Marca", "Modelo", "Total", "Com Selo", "Sem Selo"])
    linhas = [[l["material"], l["marca"], l["modelo"], l["total"], l["com_selo"], l["sem_selo"]] for l in dados["linhas"]]
    fim = _linhas_tabela(ws2, 6, linhas)
    _ajustar_colunas(ws2, [35, 20, 20, 10, 12, 12])
    ws2.auto_filter.ref = f"A5:F{fim - 1}"

    # --- Aba 3: NECESSIDADE DE SELOS ---
    ws3 = wb.create_sheet("NECESSIDADE DE SELOS")
    _cabecalho_aba(ws3, "Materiais que Precisam de Selo")
    _cabecalho_tabela(ws3, 5, ["Material", "Marca", "Modelo", "Selo Necessário"])
    linhas_selo = [[l["material"], l["marca"], l["modelo"], l["sem_selo"]] for l in dados["linhas"] if l["sem_selo"] > 0]
    fim = _linhas_tabela(ws3, 6, linhas_selo)
    _ajustar_colunas(ws3, [35, 20, 20, 16])
    ws3.auto_filter.ref = f"A5:D{fim - 1}"

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ====================================================================
# EXCEL 2 — DETALHADO INTERNO
# ====================================================================
def gerar_excel_detalhado(dados: dict) -> BytesIO:
    wb = Workbook()

    # --- Aba 1: RESUMO GERAL ---
    ws = wb.active
    ws.title = "RESUMO GERAL"
    _cabecalho_aba(ws, "RELATÓRIO DETALHADO INTERNO")
    resumo = [
        ["Data de emissão", dados["data_emissao"]],
        ["Total de itens", dados["total_geral"]],
        ["Com selo", dados["total_com_selo"]],
        ["Sem selo", dados["total_sem_selo"]],
        ["Itens danificados", dados["total_danificados"]],
        ["Necessidade de selos", dados["necessidade_selos"]],
        ["Ambientes conferidos", dados["total_ambientes_conferidos"]],
    ]
    linha = 5
    for label, valor in resumo:
        ws.cell(row=linha, column=1, value=label).font = Font(bold=True, color=AZUL)
        ws.cell(row=linha, column=2, value=valor)
        linha += 1
    _ajustar_colunas(ws, [30, 20])

    # --- Aba 2: POR MATERIAL ---
    ws2 = wb.create_sheet("POR MATERIAL")
    _cabecalho_aba(ws2, "Totais por Material")
    _cabecalho_tabela(ws2, 5, ["Material", "Total", "Com Selo", "Sem Selo"])
    linhas = [[l["material"], l["total"], l["com_selo"], l["sem_selo"]] for l in dados["por_material"]]
    fim = _linhas_tabela(ws2, 6, linhas)
    _ajustar_colunas(ws2, [35, 12, 12, 12])
    ws2.auto_filter.ref = f"A5:D{fim - 1}"

    # --- Aba 3: POR MARCA E MODELO ---
    ws3 = wb.create_sheet("POR MARCA E MODELO")
    _cabecalho_aba(ws3, "Totais por Marca e Modelo")
    _cabecalho_tabela(ws3, 5, ["Material", "Marca", "Modelo", "Total", "Com Selo", "Sem Selo"])
    linhas = [[l["material"], l["marca"], l["modelo"], l["total"], l["com_selo"], l["sem_selo"]] for l in dados["por_marca_modelo"]]
    fim = _linhas_tabela(ws3, 6, linhas)
    _ajustar_colunas(ws3, [30, 18, 18, 10, 12, 12])
    ws3.auto_filter.ref = f"A5:F{fim - 1}"

    # --- Aba 4: POR AMBIENTE ---
    ws4 = wb.create_sheet("POR AMBIENTE")
    _cabecalho_aba(ws4, "Detalhamento por Ambiente")
    _cabecalho_tabela(ws4, 5, ["Ambiente", "Bloco/Setor", "Responsável", "Material", "Marca", "Modelo", "Total", "Com Selo", "Sem Selo", "Danificados"])
    linha = 6
    for amb in dados["ambientes"]:
        for i in amb["itens"]:
            dados_linha = [
                amb["ambiente"], amb["bloco_setor"], amb["responsavel"],
                i["material"], i["marca"], i["modelo"],
                i["total"], i["com_selo"], i["sem_selo"], i["qtd_danificada"],
            ]
            for col, valor in enumerate(dados_linha, start=1):
                cell = ws4.cell(row=linha, column=col, value=valor)
                cell.border = BORDA
                cell.alignment = Alignment(vertical="center", wrap_text=True)
            linha += 1
    _ajustar_colunas(ws4, [22, 16, 22, 25, 15, 15, 10, 12, 12, 12])

    # --- Aba 5: NECESSIDADE DE SELOS ---
    ws5 = wb.create_sheet("NECESSIDADE DE SELOS")
    _cabecalho_aba(ws5, "Itens que Precisam de Selo")
    _cabecalho_tabela(ws5, 5, ["Material", "Marca", "Modelo", "Sem Selo"])
    linhas = [[l["material"], l["marca"], l["modelo"], l["sem_selo"]] for l in dados["por_marca_modelo"] if l["sem_selo"] > 0]
    _linhas_tabela(ws5, 6, linhas)
    _ajustar_colunas(ws5, [35, 18, 18, 12])

    # --- Aba 6: CONFERÊNCIA DOS AMBIENTES ---
    ws6 = wb.create_sheet("CONFERÊNCIA DOS AMBIENTES")
    _cabecalho_aba(ws6, "Situação dos Ambientes")
    _cabecalho_tabela(ws6, 5, ["Ambiente", "Bloco/Setor", "Responsável", "Status", "Itens", "Com Selo", "Sem Selo", "Danificados"])
    linhas = []
    for amb in dados["ambientes"]:
        linhas.append([
            amb["ambiente"], amb["bloco_setor"], amb["responsavel"], amb["status"],
            amb["subtotal"]["total"], amb["subtotal"]["com_selo"],
            amb["subtotal"]["sem_selo"], amb["subtotal"]["qtd_danificada"],
        ])
    fim = _linhas_tabela(ws6, 6, linhas)
    _ajustar_colunas(ws6, [22, 16, 22, 15, 10, 12, 12, 12])
    ws6.auto_filter.ref = f"A5:H{fim - 1}"

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ====================================================================
# EXCEL 3 — MATERIAIS DANIFICADOS
# ====================================================================
def gerar_excel_danos(dados: dict) -> BytesIO:
    wb = Workbook()

    # --- Aba 1: RESUMO DE DANOS ---
    ws = wb.active
    ws.title = "RESUMO DE DANOS"
    _cabecalho_aba(ws, "Resumo de Materiais Danificados")
    resumo = [
        ["Data de emissão", dados["data_emissao"]],
        ["Total de itens danificados", dados["total_itens_danificados"]],
        ["Total de ocorrências", dados["total_ocorrencias"]],
    ]
    linha = 5
    for label, valor in resumo:
        ws.cell(row=linha, column=1, value=label).font = Font(bold=True, color=AZUL)
        ws.cell(row=linha, column=2, value=valor)
        linha += 1
    _ajustar_colunas(ws, [32, 20])

    # --- Aba 2: MATERIAIS DANIFICADOS ---
    ws2 = wb.create_sheet("MATERIAIS DANIFICADOS")
    _cabecalho_aba(ws2, "Detalhamento dos Materiais Danificados")
    _cabecalho_tabela(ws2, 5, [
        "Material", "Marca", "Modelo", "Ambiente",
        "Qtd Danificada", "Descrição", "Observação",
        "Com Selo", "Sem Selo", "Responsável",
    ])
    linhas = [
        [
            l["material"], l["marca"], l["modelo"], l["ambiente"],
            l["qtd_danificada"], l["descricao"], l["observacao"],
            l["com_selo"], l["sem_selo"], l["responsavel"],
        ]
        for l in dados["linhas"]
    ]
    fim = _linhas_tabela(ws2, 6, linhas)
    _ajustar_colunas(ws2, [25, 15, 15, 20, 14, 30, 25, 10, 10, 22])
    ws2.auto_filter.ref = f"A5:J{fim - 1}"

    # --- Aba 3: POR AMBIENTE ---
    ws3 = wb.create_sheet("POR AMBIENTE")
    _cabecalho_aba(ws3, "Danos por Ambiente")
    _cabecalho_tabela(ws3, 5, ["Ambiente", "Qtd Danificada", "Ocorrências"])
    linhas = [[a["ambiente"], a["qtd"], a["ocorrencias"]] for a in dados["por_ambiente"]]
    fim = _linhas_tabela(ws3, 6, linhas)
    _ajustar_colunas(ws3, [30, 16, 15])
    ws3.auto_filter.ref = f"A5:C{fim - 1}"

    # --- Aba 4: POR TIPO DE MATERIAL ---
    ws4 = wb.create_sheet("POR TIPO DE MATERIAL")
    _cabecalho_aba(ws4, "Danos por Tipo de Material")
    _cabecalho_tabela(ws4, 5, ["Material", "Qtd Danificada", "Ocorrências"])
    linhas = [[t["material"], t["qtd"], t["ocorrencias"]] for t in dados["por_tipo"]]
    fim = _linhas_tabela(ws4, 6, linhas)
    _ajustar_colunas(ws4, [30, 16, 15])
    ws4.auto_filter.ref = f"A5:C{fim - 1}"

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf