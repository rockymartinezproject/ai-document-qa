"""Generate a small PDF with extractable text for E2E tests."""

from pathlib import Path

from fpdf import FPDF


class SamplePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "AI Document Q&A - Sample Document", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def main() -> None:
    pdf = SamplePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    paragraphs = [
        "This is a sample document used by the end-to-end test suite.",
        "The AI Document Q&A system can upload PDFs, extract their text, chunk it, "
        "and answer questions using retrieval-augmented generation.",
        "Key fact for testing: the fastest land animal is the cheetah.",
        "Another key fact: the capital of France is Paris.",
        "If the RAG pipeline works, asking 'What is the capital of France?' "
        "should retrieve the chunk mentioning Paris and include it in the answer.",
    ]

    for paragraph in paragraphs:
        pdf.multi_cell(0, 8, paragraph)
        pdf.ln(2)

    output = Path(__file__).with_suffix(".pdf")
    pdf.output(str(output))
    print(f"Generated {output}")


if __name__ == "__main__":
    main()
