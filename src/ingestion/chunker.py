"""
Estrategias de chunking para preparar documentos para indexación en FAISS.
Produce chunks con metadata enriquecida para rastreo de fuentes.
"""
from dataclasses import dataclass, field
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.config.settings import Settings, get_settings
from src.ingestion.document_loader import LoadedDocument
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class DocumentChunk:
    """Representa un chunk de texto listo para ser vectorizado e indexado."""

    chunk_id: str
    doc_id: str
    file_name: str
    source_category: str
    country: str
    text: str
    chunk_index: int
    total_chunks: int
    metadata: dict = field(default_factory=dict)


class DocumentChunker:
    """
    Divide documentos en chunks con metadata para indexación RAG.
    Usa RecursiveCharacterTextSplitter de LangChain.
    """

    def __init__(self, settings: Settings = None) -> None:
        """
        Inicializa el chunker con la configuración del sistema.

        Args:
            settings: Configuración del sistema. Si es None, usa el singleton global.
        """
        self._settings = settings or get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        logger.info(
            "DocumentChunker inicializado: chunk_size=%d, overlap=%d",
            self._settings.chunk_size,
            self._settings.chunk_overlap,
        )

    def chunk_document(self, document: LoadedDocument) -> List[DocumentChunk]:
        """
        Divide un LoadedDocument en chunks con metadata completa.

        Args:
            document: Documento cargado a dividir.

        Returns:
            Lista de DocumentChunk listos para vectorización.
        """
        if not document.raw_text.strip():
            logger.warning("Documento %s sin texto, saltando chunking", document.file_name)
            return []

        raw_chunks = self._splitter.split_text(document.raw_text)
        chunks = []

        for idx, text in enumerate(raw_chunks):
            chunk_id = f"{document.doc_id}_chunk_{idx:04d}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=document.doc_id,
                    file_name=document.file_name,
                    source_category=document.source_category.value,
                    country=document.country or "desconocido",
                    text=text,
                    chunk_index=idx,
                    total_chunks=len(raw_chunks),
                    metadata={
                        **document.metadata,
                        "chunk_id": chunk_id,
                        "chunk_index": idx,
                        "total_chunks": len(raw_chunks),
                        "char_length": len(text),
                    },
                )
            )

        logger.info(
            "Documento %s dividido en %d chunks", document.file_name, len(chunks)
        )
        return chunks

    def chunk_documents(self, documents: List[LoadedDocument]) -> List[DocumentChunk]:
        """
        Divide una lista de documentos en chunks.

        Args:
            documents: Lista de documentos a dividir.

        Returns:
            Lista combinada de todos los chunks.
        """
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        logger.info(
            "Total: %d documentos → %d chunks", len(documents), len(all_chunks)
        )
        return all_chunks
