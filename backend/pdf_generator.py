from __future__ import annotations

from pathlib import Path
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader

from models import DadosExtraidos


def generate_pdf(output_path: Path, iptu: str, dados: DadosExtraidos) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    bg = colors.HexColor("#0A0E0D")
    fg = colors.HexColor("#F4F4F5")
    emerald = colors.HexColor("#10B981")
    muted = colors.HexColor("#9CA3AF")

    c.setFillColor(bg)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    c.setTitle("UrbanFlow - Relatorio")

    def draw_logo(x: float, y: float) -> None:
        c.setStrokeColor(emerald)
        c.setLineWidth(1)
        c.circle(x + 6 * mm, y - 3 * mm, 5 * mm, stroke=1, fill=0)
        c.setFillColor(emerald)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + 6 * mm, y - 6.2 * mm, "U")
        c.setFillColor(fg)

    header_y = height - 18 * mm
    draw_logo(20 * mm, header_y + 4 * mm)
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(34 * mm, header_y, "UrbanFlow")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(34 * mm, header_y - 7 * mm, "Ficha Tecnica de Viabilidade Urbanistica")

    c.setFont("Helvetica", 10)
    c.setFillColor(muted)
    c.drawString(24 * mm, height - 34 * mm, f"IPTU (SQL): {dados.sql or iptu}")
    c.setFillColor(fg)

    y = height - 48 * mm
    line_gap = 7 * mm

    def write_section(title: str):
        nonlocal y
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(emerald)
        c.drawString(24 * mm, y, title)
        y -= 2.5 * mm
        c.setStrokeColor(emerald)
        c.setLineWidth(0.4)
        c.line(24 * mm, y, width - 24 * mm, y)
        c.setFillColor(fg)
        y -= 5 * mm

    def write_field(label: str, value: str):
        nonlocal y
        c.setFont("Helvetica-Bold", 9)
        c.drawString(24 * mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        value_text = value or "-"
        y = draw_wrapped_text(
            24 * mm + 52 * mm,
            y,
            value_text,
            width - (24 * mm + 52 * mm) - 24 * mm,
            "Helvetica",
            9,
            4 * mm,
        )
        y -= 2 * mm

    def draw_wrapped_text(x: float, y_pos: float, text: str, max_width: float, font_name: str, font_size: float, leading: float) -> float:
        c.setFont(font_name, font_size)
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
                line = test
                continue
            c.drawString(x, y_pos, line)
            y_pos -= leading
            line = word
        if line:
            c.drawString(x, y_pos, line)
            y_pos -= leading
        return y_pos

    write_section("A. Identificacao do Imovel")
    write_field("Endereco Completo", dados.enderecoCompleto)
    write_field("Bairro", dados.bairro)
    write_field("Subprefeitura", dados.subprefeitura)
    write_field("Area do Terreno (m2)", dados.areaTerreno)

    write_section("B. Parametros de Zoneamento")
    if dados.zonaSigla and dados.zonaNome:
        write_field("Sigla da Zona", f"{dados.zonaSigla} ({dados.zonaNome})")
    else:
        write_field("Sigla da Zona", dados.zonaSigla)
        write_field("Nome da Zona", dados.zonaNome)
    write_field("Lei Vigente", dados.leiVigente)
    write_field("Macroarea", dados.macroarea)

    write_section("C. Indices Urbanisticos")
    write_field("C.A. Minimo", dados.caMin)
    write_field("C.A. Basico", dados.caBasico)
    write_field("C.A. Maximo", dados.caMax)
    write_field("Taxa de Ocupacao", dados.taxaOcupacao)
    write_field("Gabarito de Altura", dados.gabaritoAltura)
    write_field("Recuos Minimos", dados.recuos)

    write_section("D. Restricoes e Alertas")
    write_field("Patrimonio Historico", dados.restricaoPatrimonio)
    write_field("Area de Manancial", dados.restricaoManancial)
    write_field("Protecao Aeroportuaria", dados.restricaoAeroportuaria)
    write_field("Melhoramento Publico", dados.restricaoMelhoramento)

    if dados.observacoes:
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(muted)
        c.drawString(24 * mm, y, f"Observacoes: {dados.observacoes}")
        c.setFillColor(fg)
        y -= line_gap

    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(muted)
    draw_wrapped_text(
        24 * mm,
        18 * mm,
        "Este relatorio tem carater informativo baseado em dados publicos do GeoSampa. "
        "A confirmacao oficial deve ser feita via Certidao de Diretrizes Urbanisticas na Prefeitura.",
        width - 48 * mm,
        "Helvetica-Oblique",
        8.5,
        4 * mm,
    )
    c.showPage()

    # Map page (full page for visualization)
    if dados.mapaUrl:
        try:
            image_path = None
            image_data = None
            if dados.mapaUrl.startswith("data:image"):
                header, payload = dados.mapaUrl.split(",", 1)
                image_data = base64.b64decode(payload)
            elif "/map/" in dados.mapaUrl:
                map_id = dados.mapaUrl.split("/map/")[-1].split("?")[0]
                image_path = Path(__file__).resolve().parent.parent / "output" / "maps" / f"{map_id}.png"
            else:
                image_path = Path(dados.mapaUrl)

            if image_data or (image_path and image_path.exists()):
                c.setFillColor(bg)
                c.rect(0, 0, width, height, stroke=0, fill=1)
                c.setFillColor(fg)
                c.setFont("Helvetica-Bold", 15)
                c.drawString(24 * mm, height - 24 * mm, "Mapa e Contexto Urbano")
                c.setStrokeColor(emerald)
                c.setLineWidth(0.4)
                c.line(24 * mm, height - 26 * mm, width - 24 * mm, height - 26 * mm)

                if dados.areaTerreno:
                    c.setFont("Helvetica", 9)
                    c.setFillColor(colors.HexColor("#9CA3AF"))
                    c.drawString(24 * mm, height - 32 * mm, f"Area do Terreno (m2): {dados.areaTerreno}")
                    c.setFillColor(colors.HexColor("#F4F4F5"))

                img = ImageReader(image_data if image_data else str(image_path))
                img_w = width - 48 * mm
                img_h = height - 100 * mm
                x = 24 * mm
                y_img = 48 * mm

                # Drop shadow
                shadow_offset = 1.5 * mm
                c.setFillColor(colors.HexColor("#0D1110"))
                c.roundRect(x + shadow_offset, y_img - shadow_offset, img_w, img_h, 8, stroke=0, fill=1)

                # Frame with rounded corners
                c.setFillColor(colors.HexColor("#0B1210"))
                c.setStrokeColor(colors.HexColor("#1F2A25"))
                c.setLineWidth(0.6)
                c.roundRect(x, y_img, img_w, img_h, 8, stroke=1, fill=1)

                # Clip image to rounded frame
                c.saveState()
                path = c.beginPath()
                path.roundRect(x, y_img, img_w, img_h, 8)
                c.clipPath(path, stroke=0, fill=0)
                c.drawImage(img, x, y_img, width=img_w, height=img_h, preserveAspectRatio=True, mask="auto")
                c.restoreState()

                # Compass rose (simple)
                comp_r = 11 * mm
                comp_x = x + img_w - 22 * mm
                comp_y = y_img + 22 * mm
                c.setFillColor(colors.HexColor("#0A0E0D"))
                c.setStrokeColor(colors.HexColor("#10B981"))
                c.setLineWidth(0.7)
                c.circle(comp_x, comp_y, comp_r, stroke=1, fill=1)
                c.setFillColor(colors.HexColor("#10B981"))
                # North arrow
                c.line(comp_x, comp_y, comp_x, comp_y + comp_r - 2)
                c.line(comp_x - 2, comp_y + comp_r - 4, comp_x, comp_y + comp_r - 1)
                c.line(comp_x + 2, comp_y + comp_r - 4, comp_x, comp_y + comp_r - 1)
                c.setFont("Helvetica-Bold", 7.5)
                c.drawCentredString(comp_x, comp_y + comp_r + 2, "N")
                c.drawCentredString(comp_x, comp_y - comp_r - 6, "S")
                c.drawString(comp_x + comp_r + 2, comp_y - 2, "E")
                c.drawString(comp_x - comp_r - 6, comp_y - 2, "W")
                c.setFillColor(fg)

                # Bottom info bar
                bar_x = 24 * mm
                bar_y = 20 * mm
                bar_w = width - 48 * mm
                bar_h = 18 * mm
                c.setFillColor(colors.HexColor("#0B1210"))
                c.setStrokeColor(colors.HexColor("#1F2A25"))
                c.roundRect(bar_x, bar_y, bar_w, bar_h, 4, stroke=1, fill=1)

                pad = 4 * mm
                left_w = bar_w * 0.55
                mid_w = bar_w * 0.20
                right_w = bar_w * 0.25

                left_x = bar_x + pad
                mid_x = bar_x + left_w + pad
                right_x = bar_x + left_w + mid_w + pad

                # Left: authenticity info
                c.setFont("Helvetica", 8)
                c.setFillColor(colors.HexColor("#9CA3AF"))
                c.drawString(left_x, bar_y + bar_h - 5 * mm, f"IPTU (SQL): {dados.sql or iptu}")
                endereco = dados.enderecoCompleto or "Endereco nao identificado"
                draw_wrapped_text(
                    left_x,
                    bar_y + bar_h - 9 * mm,
                    f"Endereco Completo: {endereco}",
                    left_w - 2 * pad,
                    "Helvetica",
                    8,
                    3.6 * mm,
                )

                # Center: zone legend
                if dados.zonaSigla:
                    zone_sigla = dados.zonaSigla.strip().upper()
                    zone_nome = dados.zonaNome.strip() if dados.zonaNome else ""
                    if zone_sigla == "ZM":
                        color = colors.HexColor("#F59E0B")
                        label = f"Cor Laranja = {zone_nome or 'Zona Mista'} ({zone_sigla})"
                    else:
                        color = colors.HexColor("#10B981")
                        label = f"Cor = {zone_nome or zone_sigla} ({zone_sigla})"
                    c.setFillColor(color)
                    c.rect(mid_x, bar_y + bar_h - 7 * mm, 4 * mm, 4 * mm, stroke=0, fill=1)
                    c.setFillColor(colors.HexColor("#F4F4F5"))
                    c.setFont("Helvetica", 7.3)
                    draw_wrapped_text(
                        mid_x + 5.5 * mm,
                        bar_y + bar_h - 6.5 * mm,
                        label,
                        mid_w - 6 * mm,
                        "Helvetica",
                        7.3,
                        3.2 * mm,
                    )

                # Right: dimensions
                if dados.dimensoesLote:
                    c.setFont("Helvetica-Bold", 8.3)
                    c.setFillColor(colors.HexColor("#10B981"))
                    c.drawString(right_x, bar_y + bar_h - 5 * mm, "Dimensoes do Lote:")
                    c.setFont("Helvetica", 7.9)
                    c.setFillColor(colors.HexColor("#F4F4F5"))
                    y_dim = bar_y + bar_h - 9 * mm
                    for item in dados.dimensoesLote[:4]:
                        c.drawString(right_x, y_dim, f"- {item}")
                        y_dim -= 3.2 * mm
                c.showPage()
        except Exception:
            pass

    # Glossario (pagina final)
    c.setFillColor(bg)
    c.rect(0, 0, width, height, stroke=0, fill=1)
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(24 * mm, height - 24 * mm, "Guia de Termos e Indices Urbanisticos")
    c.setStrokeColor(emerald)
    c.setLineWidth(0.4)
    c.line(24 * mm, height - 26 * mm, width - 24 * mm, height - 26 * mm)

    y2 = height - 40 * mm
    line_gap2 = 8 * mm

    def gloss(label: str, text: str):
        nonlocal y2
        # Small icon for quick scanning
        icon_x = 24 * mm
        icon_y = y2 + 1.5 * mm
        c.setFillColor(emerald)
        c.circle(icon_x + 2.2 * mm, icon_y, 1.6 * mm, stroke=0, fill=1)
        c.setFillColor(bg)
        c.circle(icon_x + 2.2 * mm, icon_y, 0.7 * mm, stroke=0, fill=1)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(emerald)
        c.drawString(24 * mm + 6 * mm, y2, label)
        y2 -= 4 * mm
        c.setFillColor(fg)
        y2 = draw_wrapped_text(
            24 * mm + 6 * mm,
            y2,
            text,
            width - 48 * mm - 6 * mm,
            "Helvetica",
            9.5,
            4 * mm,
        )
        y2 -= 4 * mm

    gloss("C.A. (Coeficiente de Aproveitamento)", "Fator que, multiplicado pela area do terreno, indica a metragem quadrada maxima que se pode construir.")
    gloss("Basico", "O que se pode construir sem pagar taxas extras.")
    gloss("Maximo", "O limite absoluto de construcao permitida mediante pagamento (Outorga Onerosa).")
    gloss("T.O. (Taxa de Ocupacao)", "A porcentagem maxima do terreno que pode ser ocupada pela projecao da edificacao (o contorno do predio no chao).")
    gloss("Gabarito de Altura", "A altura maxima permitida para a edificacao, medida a partir do nivel do solo.")
    gloss("Recuos", "As distancias minimas que a construcao deve manter em relacao as divisas do lote (frente, laterais e fundos).")
    gloss("Frente (Testada)", "A largura do lote que faz divisa com a via publica (calcada).")
    gloss("Zoneamento (Siglas)", "As siglas (Ex: ZM, ZEU, ZPI) representam a categoria de uso do solo, definindo se a area e residencial, comercial, industrial ou mista.")

    c.save()
