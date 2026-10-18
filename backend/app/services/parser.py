from pathlib import Path
from pypdf import PdfReader

def extract_text_from_pdf(file_path:str) -> str:
    """
    Extract text from all pages of a pdf"""

    path=Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"pdf not found:{file_path}"
        )
    reader=PdfReader(str(path))
    pages=[]
    for page in reader.pages:
        text=page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages).strip()        
