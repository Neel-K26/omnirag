import fitz

from ingestion.chunking import chunk_text
from ingestion.embeddings import embed_texts, get_embedding_dim
from ingestion.parsers import extract_text_from_html, parse_pdf, parse_text
from ingestion.store import VectorStore
from models.schemas import Chunk, ChunkMetadata, DocumentSourceType

SAMPLE_PAGE_1 = (
    "Hypertension is a chronic medical condition in which the blood pressure "
    "in the arteries is persistently elevated. It is a major risk factor for "
    "cardiovascular disease including stroke, heart failure, and kidney disease. "
    "Lifestyle changes such as reduced sodium intake, regular exercise, and weight "
    "management are commonly recommended as first-line interventions."
)
SAMPLE_PAGE_2 = (
    "Pharmacological treatment of hypertension often includes ACE inhibitors, "
    "calcium channel blockers, diuretics, and beta blockers. The choice of agent "
    "depends on patient comorbidities, age, and tolerance of side effects."
)


def _make_pdf_bytes(pages_text: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def test_chunk_text_respects_size_and_overlap():
    text = "word " * 300
    chunks = chunk_text(text, chunk_size=512, overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 512


def test_chunk_text_short_text_single_chunk():
    assert chunk_text("short text here", chunk_size=512, overlap=50) == ["short text here"]


def test_chunk_text_rejects_overlap_gte_chunk_size():
    try:
        chunk_text("some text", chunk_size=10, overlap=10)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_parse_pdf_extracts_pages():
    pdf_bytes = _make_pdf_bytes([SAMPLE_PAGE_1, SAMPLE_PAGE_2])
    pages = parse_pdf(pdf_bytes)
    assert len(pages) == 2
    assert pages[0][0] == 1
    assert "Hypertension" in pages[0][1]
    assert pages[1][0] == 2
    assert "ACE inhibitors" in pages[1][1]


def test_parse_text_strips_whitespace():
    assert parse_text("  hello world  \n") == "hello world"


def test_extract_text_from_html_strips_scripts():
    html = "<html><body><script>bad()</script><p>Clinical summary text.</p></body></html>"
    text = extract_text_from_html(html)
    assert "Clinical summary text." in text
    assert "bad()" not in text


def test_embed_texts_shape():
    embeddings = embed_texts(["hello world", "clinical trial results"])
    assert embeddings.shape == (2, get_embedding_dim())


def test_vector_store_dense_and_sparse_search(tmp_path):
    texts = [
        "Hypertension increases the risk of stroke and heart disease.",
        "Diabetes mellitus is characterized by elevated blood glucose levels.",
        "Regular exercise improves cardiovascular health outcomes.",
    ]
    chunks = [
        Chunk(
            id=str(i),
            text=t,
            metadata=ChunkMetadata(
                document_id="doc1",
                document_title="Test Doc",
                source_type=DocumentSourceType.text,
                page=None,
                chunk_index=i,
            ),
        )
        for i, t in enumerate(texts)
    ]
    embeddings = embed_texts(texts)
    store = VectorStore(dim=embeddings.shape[1])
    store.add(chunks, embeddings)

    query_embedding = embed_texts(["What raises the risk of stroke?"])[0]
    dense_results = store.search_dense(query_embedding, top_k=3)
    assert dense_results[0][0].text.startswith("Hypertension")

    sparse_results = store.search_sparse("stroke heart disease", top_k=3)
    assert any("stroke" in c.text.lower() for c, _ in sparse_results)

    save_dir = tmp_path / "index"
    store.save(save_dir)
    loaded = VectorStore.load(save_dir, dim=embeddings.shape[1])
    assert loaded.size == store.size
    assert loaded.search_dense(query_embedding, top_k=1)[0][0].text == dense_results[0][0].text
