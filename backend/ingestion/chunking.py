def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Character-based sliding window, snapped to word boundaries where possible."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap
    length = len(text)
    start = 0

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            snapped = text.rfind(" ", start, end)
            if snapped > start:
                end = snapped
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start += step

    return chunks
