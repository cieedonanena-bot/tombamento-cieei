"""
Geração de relatórios em PDF com ReportLab.
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

AZUL_MARINHO = colors.HexColor("#173C70")
AZUL_CLARO = colors.HexColor("#DBEAFE")
CINZA_CLARO = colors.HexColor("#F3F6FA")
CINZA_BORDA = colors.HexColor("#E2E8F0")

INSTITUICAO = (
    "CENTRO INTEGRADO DE EDUCAÇÃO ESPECIAL E ENSINO INFANTIL "
    "DONA NENA – CIEEI"
)


def _estilos():
    s = getSampleStyleSheet()
    return {
        "instituicao": ParagraphStyle(
            "inst", parent=s["Normal"], fontSize=11, leading=14,
            alignment=1, textColor=AZUL_MARINHO, fontName="Helvetica-Bold"
        ),
        "titulo": ParagraphStyle(
            "tit", parent=s["Heading1"], fontSize=16, alignment=1,
            textColor=AZUL_MARINHO, spaceAfter=6, spaceBefore=4
        ),
        "subtitulo": ParagraphStyle(
            "sub", parent=s["Normal"], fontSize=9, alignment=1,
            textColor=colors.HexColor("#64748B"), spaceAfter=14
        ),
        "secao": ParagraphStyle(
            "sec", parent=s["Heading2"], fontSize=12, textColor=AZUL_MARINHO,
            spaceBefore=14, spaceAfter=8
        ),
        "normal": ParagraphStyle("nor", parent=s["Normal"], fontSize=9, leading=11),
        "rodape": ParagraphStyle(
            "rod", parent=s["Normal"], fontSize=8, alignment=1,
            textColor=colors.HexColor("#64748B")
        ),
    }


def _cabecalho(titulo: str, subtitulo: str, data_emissao: str) -> list:
    est = _estilos()
    return [
        Paragraph(INSTITUICAO, est["instituicao"]),
        Spacer(1, 0.3 * cm),
        Paragraph(titulo, est["titulo"]),
        Paragraph(subtitulo, est["subtitulo"]),
        Paragraph(f"<b>Data de emissão:</b> {data_emissao}", est["normal"]),
        Spacer(1, 0.5 * cm),
    ]


def _tabela(cabecalhos: list, linhas: list, larguras: list | None = None) -> Table:
    dados = [cabecalhos] + linhas
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_MARINHO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _totais_rodape(total_geral: int, com_selo: int, sem_selo: int, necessidade: int) -> list:
    est = _estilos()
    return [
        Spacer(1, 0.4 * cm),
        Paragraph(
            f"<b>Total geral:</b> {total_geral} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Com selo:</b> {com_selo} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Sem selo:</b> {sem_selo} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Necessidade de selos:</b> {necessidade}",
            est["normal"]
        ),
    ]


# ====================================================================
# PDF 1 — OFICIAL DE TOMBAMENTO
# ====================================================================
def gerar_pdf_oficial(dados: dict) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    est = _estilos()
    story = _cabecalho(
        "RELATÓRIO GERAL DE LEVANTAMENTO PATRIMONIAL",
        "Documento oficial — agrupado por material, marca e modelo",
        dados["data_emissao"],
    )

    linhas = [
        [l["material"], l["marca"], l["modelo"], l["total"], l["com_selo"], l["sem_selo"]]
        for l in dados["linhas"]
    ]
    if not linhas:
        story.append(Paragraph("Nenhum dado registrado.", est["normal"]))
    else:
        story.append(_tabela(
            ["Material", "Marca", "Modelo", "Total", "Com Selo", "Sem Selo"],
            linhas,
            larguras=[5.5 * cm, 3 * cm, 3 * cm, 1.8 * cm, 2 * cm, 2 * cm],
        ))
        story.extend(_totais_rodape(
            dados["total_geral"], dados["total_com_selo"],
            dados["total_sem_selo"], dados["necessidade_selos"],
        ))

    # Assinatura
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph("_" * 60, est["rodape"]))
    story.append(Paragraph("Assinatura do(a) Responsável", est["rodape"]))

    doc.build(story)
    buf.seek(0)
    return buf


# ====================================================================
# PDF 2 — DETALHADO INTERNO
# ====================================================================
def gerar_pdf_detalhado(dados: dict) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    est = _estilos()
    story = _cabecalho(
        "RELATÓRIO DETALHADO INTERNO",
        "Documento de uso interno — organizado por ambiente",
        dados["data_emissao"],
    )

    if not dados["ambientes"]:
        story.append(Paragraph("Nenhuma conferência registrada.", est["normal"]))
    else:
        for amb in dados["ambientes"]:
            story.append(Paragraph(f"Ambiente: {amb['ambiente']}", est["secao"]))
            story.append(Paragraph(
                f"<b>Bloco/Setor:</b> {amb['bloco_setor']} &nbsp;|&nbsp; "
                f"<b>Situação:</b> {amb['status']} &nbsp;|&nbsp; "
                f"<b>Responsável:</b> {amb['responsavel']}",
                est["normal"]
            ))
            story.append(Spacer(1, 0.2 * cm))

            linhas = [
                [
                    i["material"], i["marca"], i["modelo"],
                    i["total"], i["com_selo"], i["sem_selo"],
                    i["qtd_danificada"], (i["descricao_danos"] or "—")[:40]
                ]
                for i in amb["itens"]
            ]
            story.append(_tabela(
                ["Material", "Marca", "Modelo", "Tot", "C/", "S/", "Dan", "Descrição"],
                linhas,
                larguras=[4 * cm, 2.5 * cm, 2.5 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm, 4 * cm],
            ))
            st = amb["subtotal"]
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(
                f"<b>Subtotal:</b> {st['total']} itens | "
                f"Com selo: {st['com_selo']} | Sem selo: {st['sem_selo']} | "
                f"Danificados: {st['qtd_danificada']}",
                est["normal"]
            ))
            story.append(Spacer(1, 0.5 * cm))

        story.append(PageBreak())
        story.append(Paragraph("TOTAIS GERAIS", est["titulo"]))
        story.extend(_totais_rodape(
            dados["total_geral"], dados["total_com_selo"],
            dados["total_sem_selo"], dados["necessidade_selos"],
        ))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            f"<b>Total de itens danificados:</b> {dados['total_danificados']}",
            est["normal"]
        ))

    doc.build(story)
    buf.seek(0)
    return buf


# ====================================================================
# PDF 3 — MATERIAIS DANIFICADOS
# ====================================================================
def gerar_pdf_danos(dados: dict) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    est = _estilos()
    story = _cabecalho(
        "RELATÓRIO DE MATERIAIS DANIFICADOS",
        "Apenas itens com dano declarado — uso interno",
        dados["data_emissao"],
    )

    if not dados["linhas"]:
        story.append(Paragraph("Nenhum material danificado registrado.", est["normal"]))
    else:
        linhas = [
            [
                l["material"], l["marca"], l["modelo"], l["ambiente"],
                l["qtd_danificada"], (l["descricao"] or "")[:35],
                (l["observacao"] or "—")[:30],
                l["com_selo"], l["sem_selo"], l["responsavel"],
            ]
            for l in dados["linhas"]
        ]
        story.append(_tabela(
            ["Material", "Marca", "Modelo", "Ambiente", "Qtd", "Descrição", "Observação", "C/Selo", "S/Selo", "Responsável"],
            linhas,
            larguras=[3.5 * cm, 2 * cm, 2 * cm, 3 * cm, 1.2 * cm, 5 * cm, 4.5 * cm, 1.5 * cm, 1.5 * cm, 3 * cm],
        ))
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph(
            f"<b>Total de itens danificados:</b> {dados['total_itens_danificados']} "
            f"&nbsp;|&nbsp; <b>Total de ocorrências:</b> {dados['total_ocorrencias']}",
            est["normal"]
        ))

    doc.build(story)
    buf.seek(0)
    return buf