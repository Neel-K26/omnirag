import json
from functools import lru_cache
from pathlib import Path

from models.schemas import Document

REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "index" / "documents.json"


class DocumentRegistry:
    def __init__(self):
        self.documents: list[Document] = []

    def add(self, document: Document) -> None:
        self.documents.append(document)

    def list(self) -> list[Document]:
        return list(self.documents)

    def save(self, path: Path = REGISTRY_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([d.model_dump(mode="json") for d in self.documents]))

    @classmethod
    def load(cls, path: Path = REGISTRY_PATH) -> "DocumentRegistry":
        registry = cls()
        if path.exists():
            data = json.loads(path.read_text())
            registry.documents = [Document(**d) for d in data]
        return registry


@lru_cache
def get_document_registry() -> DocumentRegistry:
    return DocumentRegistry.load()
