from pathlib import Path
from app.services.parser import extract_text_from_pdf

def test_extract_text_from_pdf():
    pdf_path = (
        Path(__file__).parent.parent
        / "test_data"
        / "Jagadeesh_Gowda_AI_Engineer_Resume.pdf"
    )

    if not pdf_path.exists():
        import pytest
        pytest.skip(f"Test PDF not found: {pdf_path}")

    text = extract_text_from_pdf(str(pdf_path))

    assert isinstance(text, str)
    assert text.strip(), "Expected the PDF to contain extractable text"
