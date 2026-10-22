"""
TF-IDF Document Retrieval engine using scikit-learn.
Retrieves and ranks vendor evidence chunks using cosine similarity.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import DATA_DIR, DEFAULT_TOP_K


class DocumentRetriever:
    """
    RAG-style document retriever utilizing TF-IDF Vectorization and Cosine Similarity.
    Caches vectorizers per vendor to maintain performance and reproducibility.
    """

    def __init__(self, documents_path: Optional[Path] = None):
        self.documents_path = documents_path or (DATA_DIR / "vendor_documents.json")
        self.documents_by_vendor: Dict[str, List[Dict[str, Any]]] = self._load_documents()
        self._vectorizer_cache: Dict[str, TfidfVectorizer] = {}
        self._matrix_cache: Dict[str, Any] = {}

    def _load_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.documents_path.exists():
            return {}
        with open(self.documents_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_or_create_index(self, vendor_name: str):
        if vendor_name in self._vectorizer_cache:
            return self._vectorizer_cache[vendor_name], self._matrix_cache[vendor_name]

        docs = self.documents_by_vendor.get(vendor_name, [])
        if not docs:
            return None, None

        texts = [doc["text"] for doc in docs]
        # Use sublinear tf and lowercase
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w+\b"
        )
        tfidf_matrix = vectorizer.fit_transform(texts)

        self._vectorizer_cache[vendor_name] = vectorizer
        self._matrix_cache[vendor_name] = tfidf_matrix
        return vectorizer, tfidf_matrix

    def retrieve(
        self,
        vendor_name: str,
        query: str,
        top_k: int = DEFAULT_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most relevant document chunks for the vendor given a query string.
        Returns list of chunks containing doc_id, text, score, and metadata.
        """
        docs = self.documents_by_vendor.get(vendor_name, [])
        if not docs:
            return []

        vectorizer, matrix = self._get_or_create_index(vendor_name)
        if vectorizer is None or matrix is None:
            return []

        # Vectorize query
        try:
            query_vector = vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, matrix).flatten()
        except Exception:
            # Fallback if vocabulary mismatch
            similarities = [0.0] * len(docs)

        # Pair each doc with score
        scored_docs = []
        for idx, doc in enumerate(docs):
            score = float(similarities[idx])
            scored_docs.append({
                "doc_id": doc.get("id", f"DOC-{idx}"),
                "title": doc.get("title", "Document"),
                "date": doc.get("date", "2026-01-01"),
                "category": doc.get("category", "general"),
                "text": doc.get("text", ""),
                "score": round(score, 4),
                "vendor": vendor_name
            })

        # Sort descending by score
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]
