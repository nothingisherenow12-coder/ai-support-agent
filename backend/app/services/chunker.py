import re

def clean_text(text:str)->str:
    """
    Clean extracted PDF text by removing unnecessary whitespace"""

    text=text.replace("\r","\n")
    text=re.sub(r"[\t]+"," ",text)
    text=re.sub(r"\n{3,}","\n\n",text)

    return text.strip()

def chunk_text(text:str,chunk_size:int=1000,overlap:int=200,)->list[str]:
    """
    Split text into overlapping chunks.

    chunk_size:
        Maximum approximate number of characters per chunk.

    overlap:
        Number of characters repeated between
        consecutive chunks.
    """
    if not text.strip():
        return []
    if overlap >=chunk_size:
        raise ValueError("overlap must be smaller that chunk_size")
    cleaned_text=clean_text(text)
    chunks=[]
    start=0
    while start < len(cleaned_text):
        end=start+chunk_size

        chunk=cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned_text):
            break
        start=end-overlap
        
    return chunks    



