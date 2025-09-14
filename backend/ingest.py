# ingest.py
import os
from typing import List, Dict, Any, Tuple

from pypdf import PdfReader

from backend import config
from backend.rag import GeminiClient  # NEW import


def read_pdf_with_pages(file_path: str) -> List[Tuple[int, str]]:
    pages: List[Tuple[int, str]] = []
    reader = PdfReader(file_path)
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            pages.append((i + 1, _clean_text(text)))
    return pages


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    return "\n".join(line.strip() for line in text.splitlines())


def split_into_chunks(pages: List[Tuple[int, str]], chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    buffer: List[Tuple[int, str]] = []
    current_len = 0

    def flush_chunk():
        nonlocal buffer, current_len
        if not buffer:
            return
        page_start = buffer[0][0]
        page_end = buffer[-1][0]
        content = "\n".join(t for _, t in buffer)
        chunks.append({
            "text": content,
            "page_start": page_start,
            "page_end": page_end,
        })
        # overlap
        if chunk_overlap > 0 and len(content) > chunk_overlap:
            overlap_text = content[-chunk_overlap:]
            buffer = [(page_end, overlap_text)]
            current_len = len(overlap_text)
        else:
            buffer = []
            current_len = 0

    for page_num, text in pages:
        tokens = text
        while tokens:
            remaining = chunk_size - current_len
            if remaining <= 0:
                flush_chunk()
                continue
            take = tokens[:remaining]
            buffer.append((page_num, take))
            current_len += len(take)
            tokens = tokens[remaining:]
            if current_len >= chunk_size:
                flush_chunk()

    if current_len > 0:
        flush_chunk()

    return chunks


def ingest_pdfs(pdf_dir: str | None = None) -> List[Dict[str, Any]]:
    """Ingest PDFs and return chunks"""
    base = pdf_dir or config.PDFS_DIR
    if not os.path.isdir(base):
        raise FileNotFoundError(f"PDF directory not found: {base}")

    pdf_files = [os.path.join(base, f) for f in os.listdir(base) if f.lower().endswith(".pdf")]
    pdf_files.sort()
    all_chunks: List[Dict[str, Any]] = []
    print(f"[INGEST] Found {len(pdf_files)} PDF files in {base}")
    for idx, file_path in enumerate(pdf_files, start=1):
        print(f"[INGEST] ({idx}/{len(pdf_files)}) Reading: {os.path.basename(file_path)}")
        file_pages = read_pdf_with_pages(file_path)
        print(f"[INGEST] Pages extracted: {len(file_pages)}")
        chunks = split_into_chunks(file_pages, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        print(f"[INGEST] Chunks created: {len(chunks)}")
        for ch in chunks:
            ch["source_file"] = os.path.basename(file_path)
        all_chunks.extend(chunks)
    print(f"[INGEST] Total chunks: {len(all_chunks)} from {len(pdf_files)} files")
    return all_chunks


def summarize_text(text: str, target_ratio: float = 0.1, api_key: str = None) -> str:
    """Summarize text to approximately target_ratio length"""
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set for summarization.")

    llm = GeminiClient(model_name="gemini-1.5-flash", api_key=api_key)
    prompt = (
        f"Summarize the following document into a shorter version of about {int(target_ratio*100)}% length. "
        f"Keep the key context and important points:\n\n{text}"
    )
    summary = llm.generate(prompt, max_output_tokens=2048)
    return summary
