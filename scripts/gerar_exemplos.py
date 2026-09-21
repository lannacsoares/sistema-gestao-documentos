"""Gera em exemplos/ os arquivos de teste dos casos de borda (CB01 a CB06).

Tudo é fictício e marcado como "DOCUMENTO FICTÍCIO". Uso (na raiz do projeto):
    pip install -r requirements-dev.txt
    python scripts/gerar_exemplos.py
O arquivo grande.png (~27 MB) não é versionado (.gitignore); o script o recria quando necessário.
"""
import os
import shutil
import textwrap
from pathlib import Path

from faker import Faker
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

PASTA = Path(__file__).resolve().parent.parent / "exemplos"
fake = Faker("pt_BR")
Faker.seed(2026)  # mesmos dados a cada execução


def _fonte(tamanho: int):
    for caminho in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def gerar_pdf(destino: Path) -> None:
    """PDF simples com dados inventados (sem CPF/RG reais)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "PROCURACAO (DOCUMENTO FICTICIO)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", size=12)
    pdf.ln(6)
    linhas = [
        f"Outorgante: {fake.name()}",
        f"Outorgado: {fake.name()}",
        f"Endereco: {fake.street_address()}, {fake.city()}",
        f"Data: {fake.date_this_year().strftime('%d/%m/%Y')}",
        "",
        "Este documento e ficticio e foi gerado apenas para testes do sistema.",
    ]
    for linha in linhas:
        pdf.cell(0, 9, linha, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(destino))


def gerar_laudo(destino: Path) -> None:
    """Laudo fictício de uma página, com dados inventados."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "LAUDO TECNICO (DOCUMENTO FICTICIO)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", size=12)
    pdf.ln(6)
    linhas = [
        f"Periciando: {fake.name()}",
        f"Local da vistoria: {fake.street_address()}, {fake.city()}",
        f"Data da vistoria: {fake.date_this_year().strftime('%d/%m/%Y')}",
        "",
        "Conclusao: documento inventado para demonstrar o sistema. Nenhum dado e real.",
    ]
    for linha in linhas:
        pdf.cell(0, 9, linha, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(destino))


def gerar_imagens(png: Path, jpg: Path) -> None:
    imagem = Image.new("RGB", (800, 600), "white")
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle([20, 20, 780, 580], outline="#0D3638", width=4)
    desenho.text((60, 260), "DOCUMENTO FICTICIO - TESTE", fill="#0D3638", font=_fonte(40))
    imagem.save(png)
    imagem.save(jpg, quality=90)


def gerar_comprovante_png(destino: Path) -> None:
    """Comprovante de pagamento fictício em PNG (estilo recibo)."""
    imagem = Image.new("RGB", (800, 1000), "#FBFBF8")
    d = ImageDraw.Draw(imagem)
    d.rectangle([24, 24, 776, 976], outline="#0D3638", width=3)
    d.text((60, 60), "COMPROVANTE DE PAGAMENTO", fill="#0D3638", font=_fonte(36))
    d.text((60, 112), "DOCUMENTO FICTICIO - TESTE", fill="#A03040", font=_fonte(26))
    linhas = [
        ("Pagador", fake.name()), ("Beneficiario", fake.company()),
        ("Valor", f"R$ {fake.pydecimal(left_digits=3, right_digits=2, positive=True)}".replace(".", ",")),
        ("Data", fake.date_this_year().strftime("%d/%m/%Y")), ("Autenticacao", fake.bothify("????-####-????").upper()),
    ]
    y = 220
    for rotulo, valor in linhas:
        d.text((60, y), rotulo, fill="#5A5B5D", font=_fonte(24))
        d.text((60, y + 34), valor, fill="#3A3A3A", font=_fonte(32))
        d.line([60, y + 84, 740, y + 84], fill="#D5D9DA", width=2)
        y += 120
    d.text((60, 900), "Gerado por scripts/gerar_exemplos.py. Nenhum dado e real.", fill="#5A5B5D", font=_fonte(20))
    imagem.save(destino, optimize=True)


def gerar_digitalizado_jpg(destino: Path) -> None:
    """Página fictícia 'digitalizada' em JPG: texto, ruído leve e uma pequena inclinação."""
    pagina = Image.new("RGB", (900, 1200), "#F4F3EE")
    d = ImageDraw.Draw(pagina)
    d.text((70, 80), "DECLARACAO (DOCUMENTO FICTICIO)", fill="#222222", font=_fonte(34))
    texto = (
        f"Eu, {fake.name()}, declaro para os devidos fins que este e um documento inventado, "
        "criado apenas para demonstrar o envio de imagens no sistema de gestao de documentos. "
        f"Local e data: {fake.city()}, {fake.date_this_year().strftime('%d/%m/%Y')}. "
        "Nenhuma informacao deste arquivo e real e ele nao possui valor juridico."
    )
    y = 170
    for linha in textwrap.wrap(texto, width=52):
        d.text((70, y), linha, fill="#333333", font=_fonte(26))
        y += 48
    d.text((70, 1080), "Documento ficticio para testes. Nenhum dado e real.", fill="#A03040", font=_fonte(22))
    pagina = pagina.rotate(1.2, fillcolor="#E9E8E2", expand=False)
    ruido = Image.effect_noise(pagina.size, 12).convert("RGB")
    Image.blend(pagina, ruido, 0.05).save(destino, quality=85)


def gerar_grande(destino: Path) -> None:
    """Ruído aleatório 3000x3000: não comprime, então o PNG fica com ~27 MB."""
    Image.frombytes("RGB", (3000, 3000), os.urandom(3000 * 3000 * 3)).save(destino, compress_level=1)


def main() -> None:
    PASTA.mkdir(exist_ok=True)
    pdf = PASTA / "procuracao_ficticia.pdf"
    gerar_pdf(pdf)
    gerar_laudo(PASTA / "laudo_ficticio.pdf")
    gerar_comprovante_png(PASTA / "comprovante_pagamento_ficticio.png")
    gerar_digitalizado_jpg(PASTA / "declaracao_digitalizada_ficticia.jpg")
    gerar_imagens(PASTA / "comprovante_ficticio.png", PASTA / "comprovante_ficticio.jpg")

    (PASTA / "vazio.pdf").write_bytes(b"")  # 0 bytes
    (PASTA / "falso.pdf").write_text("Isto e texto puro com extensao .pdf (DOCUMENTO FICTICIO).\n", encoding="utf-8")
    (PASTA / "nao_permitido.txt").write_text("Texto puro (DOCUMENTO FICTICIO).\n", encoding="utf-8")
    (PASTA / "nao_permitido.docx").write_bytes(b"PK\x03\x04 nao e um docx de verdade (DOCUMENTO FICTICIO)")
    shutil.copyfile(pdf, PASTA / "nome com acento e símbolos (1).pdf")

    grande = PASTA / "grande.png"
    if not grande.exists():
        gerar_grande(grande)

    # Exatamente 10 MB (o limite): PDF válido no começo, preenchido com espaços dentro de um comentário PDF.
    limite = PASTA / "exatamente_10mb.pdf"
    if not limite.exists():
        base = pdf.read_bytes()
        preenchimento = 10 * 1024 * 1024 - len(base) - 3
        limite.write_bytes(base + b"\n%" + b" " * preenchimento + b"\n")

    for arquivo in sorted(PASTA.iterdir()):
        print(f"{arquivo.stat().st_size / 1024 / 1024:8.2f} MB  {arquivo.name}")


if __name__ == "__main__":
    main()
