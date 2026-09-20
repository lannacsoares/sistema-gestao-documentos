"""Gera em exemplos/ os arquivos de teste dos casos de borda (CB01 a CB06).

Tudo é fictício e marcado como "DOCUMENTO FICTÍCIO". Uso (na raiz do projeto):
    pip install -r requirements-dev.txt
    python scripts/gerar_exemplos.py
O arquivo grande.png (~27 MB) não é versionado (.gitignore); o script o recria quando necessário.
"""
import os
import shutil
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


def gerar_grande(destino: Path) -> None:
    """Ruído aleatório 3000x3000: não comprime, então o PNG fica com ~27 MB."""
    Image.frombytes("RGB", (3000, 3000), os.urandom(3000 * 3000 * 3)).save(destino, compress_level=1)


def main() -> None:
    PASTA.mkdir(exist_ok=True)
    pdf = PASTA / "procuracao_ficticia.pdf"
    gerar_pdf(pdf)
    gerar_laudo(PASTA / "laudo_ficticio.pdf")
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
