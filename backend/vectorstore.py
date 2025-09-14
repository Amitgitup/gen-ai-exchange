import json
import os
from typing import List, Dict, Any, Tuple

import faiss
import numpy as np

from backend import config


class FaissStore:
    def __init__(self, index_path: str, metadata_path: str):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index: faiss.IndexFlatIP | None = None
        self.id_to_meta: Dict[int, Dict[str, Any]] = {}
        self._next_id: int = 0

    def _ensure_index(self, dim: int):
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)

    def load(self) -> int:
        vectors = 0
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            vectors = self.index.ntotal
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
                # keys are strings; convert to int
                self.id_to_meta = {int(k): v for k, v in payload.get("id_to_meta", {}).items()}
                self._next_id = int(payload.get("next_id", vectors))
        else:
            self.id_to_meta = {}
            self._next_id = vectors
        return vectors

    def save(self):
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump({"id_to_meta": self.id_to_meta, "next_id": self._next_id}, f, ensure_ascii=False)

    def add(self, embeddings: np.ndarray, metadatas: List[Dict[str, Any]]):
        assert embeddings.ndim == 2
        # normalize for cosine similarity using inner product
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
        embeddings = embeddings / norms
        self._ensure_index(embeddings.shape[1])
        start_id = self._next_id
        self.index.add(embeddings.astype(np.float32))
        for i, meta in enumerate(metadatas):
            self.id_to_meta[start_id + i] = meta
        self._next_id += embeddings.shape[0]

    def search(self, query_emb: np.ndarray, top_k: int) -> List[Tuple[float, Dict[str, Any]]]:
        assert query_emb.ndim == 1
        # normalize
        norm = np.linalg.norm(query_emb) + 1e-12
        q = (query_emb / norm).astype(np.float32)[None, :]
        if self.index is None or self.index.ntotal == 0:
            return []
        scores, ids = self.index.search(q, top_k)
        result: List[Tuple[float, Dict[str, Any]]] = []
        for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
            if idx == -1:
                continue
            meta = self.id_to_meta.get(idx)
            if not meta:
                continue
            result.append((float(score), meta))
        return result

    def stats(self) -> Dict[str, Any]:
        return {
            "vectors": 0 if self.index is None else int(self.index.ntotal),
            "files_indexed": len({m.get("source_file") for m in self.id_to_meta.values()}),
            "index_path": os.path.abspath(self.index_path),
            "metadata_path": os.path.abspath(self.metadata_path),
            "index_exists": os.path.exists(self.index_path),
            "last_modified": _last_modified(self.index_path),
        }


def _last_modified(path: str) -> str | None:
    try:
        if os.path.exists(path):
            ts = os.path.getmtime(path)
            from datetime import datetime
            return datetime.fromtimestamp(ts).isoformat()
        return None
    except Exception:
        return None
