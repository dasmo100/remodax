"""
Remodax - Local RAG Retrieval Infrastructure
Provides fast, lightweight, and private in-memory document chunk search.
Operates completely offline and locally without external vector databases.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Set
from src.domain.entities.document import Document, DocumentChunk
from src.domain.ports.document_port import IRAGService


class LocalRAGEngine(IRAGService):
    """
    Lightweight, fully private local RAG engine based on BM25-style term frequency.
    Ensures zero cloud document leakage while providing fast contextual chunk retrieval.
    """

    def __init__(self):
        # document_id -> List[DocumentChunk]
        self._indexed_chunks: Dict[str, List[DocumentChunk]] = {}
        self._all_chunks: List[DocumentChunk] = []

    def index_document(self, document: Document) -> None:
        """Indexes all chunks for a parsed document."""
        self._indexed_chunks[document.id] = list(document.chunks)
        self._refresh_flattened_chunks()

    def remove_document(self, document_id: str) -> None:
        """Removes all chunks of a deleted document from the active index."""
        if document_id in self._indexed_chunks:
            del self._indexed_chunks[document_id]
            self._refresh_flattened_chunks()

    def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Returns indexed chunks for a specific document."""
        return list(self._indexed_chunks.get(document_id, []))

    def search_context(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """
        Retrieves top_k relevant chunks matching the query terms using keyword scoring.
        """
        if not self._all_chunks or not query or not query.strip():
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored_chunks: List[tuple[float, DocumentChunk]] = []

        for chunk in self._all_chunks:
            chunk_tokens = self._tokenize(chunk.content)
            score = self._compute_relevance_score(query_tokens, chunk_tokens)
            if score > 0:
                chunk.relevance_score = score
                scored_chunks.append((score, chunk))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:top_k]]

    def _refresh_flattened_chunks(self) -> None:
        self._all_chunks = [
            chunk for chunk_list in self._indexed_chunks.values() for chunk in chunk_list
        ]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        words = re.findall(r"\w+", text.lower())
        # Filter out very short stop words
        return [w for w in words if len(w) > 2]

    @staticmethod
    def _compute_relevance_score(query_tokens: List[str], chunk_tokens: List[str]) -> float:
        if not chunk_tokens:
            return 0.0

        chunk_counter = Counter(chunk_tokens)
        chunk_len = len(chunk_tokens)
        score = 0.0

        for token in query_tokens:
            count = chunk_counter.get(token, 0)
            if count > 0:
                # Term frequency normalized by chunk length
                tf = count / chunk_len
                score += tf * (1.0 + math.log(1.0 + count))

        return score
