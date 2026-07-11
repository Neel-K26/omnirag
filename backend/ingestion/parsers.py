import fitz
import requests
from bs4 import BeautifulSoup


def parse_pdf(file_bytes: bytes) -> list[tuple[int, str]]:
    """Extract text per page. Returns list of (1-indexed page number, page text), skipping blank pages."""
    pages: list[tuple[int, str]] = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                pages.append((i + 1, text))
    return pages


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    return "\n".join(lines)


def parse_url(url: str, timeout: int = 15) -> str:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "OmniRAG/0.1"})
    response.raise_for_status()
    return extract_text_from_html(response.text)


def parse_text(text: str) -> str:
    return text.strip()
