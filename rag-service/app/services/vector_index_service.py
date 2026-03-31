import os
import shutil
import threading
from typing import Any

from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

from app.core.config import settings


class VectorIndexService:
    def __init__(self):
        self._store: Chroma | None = None
        self._lock = threading.Lock()

    def reindex(self, documents: list[Any]) -> dict[str, Any]:
        store = self._reset_store()
        if documents:
            store.add_documents(documents)
        return self.get_status()

    def ensure_index(self, documents_provider) -> dict[str, Any]:
        if self._count_documents() == 0:
            return self.reindex(documents_provider())
        return self.get_status()

    def similarity_search(self, query: str, top_k: int, documents_provider) -> list[Any]:
        self.ensure_index(documents_provider)
        return self._get_store().similarity_search(query, k=top_k)

    def get_status(self) -> dict[str, Any]:
        return {
            "indexed_documents": self._count_documents(),
            "persist_directory": settings.chroma_persist_directory,
            "collection_name": settings.chroma_collection_name,
        }

    def _count_documents(self) -> int:
        return self._get_store()._collection.count()

    def _reset_store(self) -> Chroma:
        shutil.rmtree(settings.chroma_persist_directory, ignore_errors=True)
        return self._get_store(force_recreate=True)

    def _get_store(self, force_recreate: bool = False) -> Chroma:
        with self._lock:
            if force_recreate:
                self._store = None
            if self._store is None:
                os.makedirs(settings.chroma_persist_directory, exist_ok=True)
                self._store = Chroma(
                    collection_name=settings.chroma_collection_name,
                    persist_directory=settings.chroma_persist_directory,
                    embedding_function=FastEmbedEmbeddings(model_name=settings.embedding_model),
                )
            return self._store