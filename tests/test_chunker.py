"""
Tests para el módulo de chunking de documentos.
"""
from unittest.mock import MagicMock

import pytest

from src.ingestion.chunker import DocumentChunker
from src.ingestion.document_loader import DocumentType, LoadedDocument, SourceCategory


def make_doc(text: str, file_name: str = "test.pdf") -> LoadedDocument:
    """Crea un LoadedDocument de prueba."""
    return LoadedDocument(
        doc_id="test_doc_001",
        file_name=file_name,
        file_path=f"/fake/{file_name}",
        doc_type=DocumentType.PDF,
        source_category=SourceCategory.INFORME_GESTION,
        country="honduras",
        pages_or_slides=1,
        raw_text=text,
        metadata={
            "source_category": "informe_gestion",
            "country": "honduras",
            "doc_type": "pdf",
            "file_name": file_name,
        },
    )


@pytest.fixture
def chunker() -> DocumentChunker:
    """Fixture con configuración de prueba."""
    settings = MagicMock()
    settings.chunk_size = 200
    settings.chunk_overlap = 20
    return DocumentChunker(settings=settings)


def test_chunk_basic(chunker: DocumentChunker) -> None:
    """Un documento largo debe producir múltiples chunks."""
    long_text = "Texto de prueba. " * 100
    doc = make_doc(long_text)
    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1


def test_chunk_metadata_propagation(chunker: DocumentChunker) -> None:
    """Los chunks deben heredar la metadata del documento original."""
    doc = make_doc("Texto de prueba suficientemente largo para generar contenido. " * 20)
    chunks = chunker.chunk_document(doc)
    for chunk in chunks:
        assert chunk.doc_id == "test_doc_001"
        assert chunk.country == "honduras"
        assert chunk.source_category == "informe_gestion"
        assert chunk.file_name == "test.pdf"


def test_chunk_empty_document(chunker: DocumentChunker) -> None:
    """Un documento sin texto debe retornar lista vacía."""
    doc = make_doc("")
    chunks = chunker.chunk_document(doc)
    assert chunks == []


def test_chunk_ids_are_unique(chunker: DocumentChunker) -> None:
    """Todos los chunk_ids deben ser únicos."""
    doc = make_doc("Texto de prueba. " * 100)
    chunks = chunker.chunk_document(doc)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
