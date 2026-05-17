from pathlib import Path

try:
    from fpdf import FPDF
except ImportError as exc:
    raise SystemExit("fpdf2 is required. Install with: python -m pip install fpdf2") from exc

ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "backend" / "seed"


def build_pdf(text: str, output_path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in text.splitlines():
        pdf.cell(0, 8, txt=line, ln=True)
    pdf.output(str(output_path))


def main() -> None:
    text_a = (SEED_DIR / "lab_results_a.txt").read_text(encoding="utf-8")
    text_b = (SEED_DIR / "lab_results_b.txt").read_text(encoding="utf-8")
    build_pdf(text_a, SEED_DIR / "lab_results_a.pdf")
    build_pdf(text_b, SEED_DIR / "lab_results_b.pdf")
    print("Generated PDFs in", SEED_DIR)


if __name__ == "__main__":
    main()
