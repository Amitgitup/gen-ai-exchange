from typing import List, Dict, Any

import numpy as np
import google.generativeai as genai

from backend import config
from backend.vectorstore import FaissStore


class EmbeddingsClient:
    def __init__(self, model_name: str, api_key: str, batch_size: int = 64):
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set. Please configure your environment.")
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.batch_size = batch_size

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 768), dtype=np.float32)
        batches: List[np.ndarray] = []
        total = len(texts)
        for i in range(0, total, self.batch_size):
            batch = texts[i:i + self.batch_size]
            print(f"[EMBED] Embedding batch {i//self.batch_size + 1}/{(total + self.batch_size - 1)//self.batch_size} (size={len(batch)})")
            resp = genai.embed_content(model=self.model_name, content=batch, task_type="retrieval_document")
            if isinstance(resp, dict) and "embeddings" in resp:
                vectors = [np.array(item["values"], dtype=np.float32) for item in resp["embeddings"]]
            elif isinstance(resp, dict) and "embedding" in resp:
                vectors = [np.array(resp["embedding"], dtype=np.float32)]
            else:
                try:
                    vecs = getattr(resp, "embeddings", None)
                    if vecs is None:
                        vecs = [getattr(resp, "embedding")]
                    vectors = [np.array(getattr(v, "values", v), dtype=np.float32) for v in vecs]
                except Exception as e:
                    raise RuntimeError(f"Unexpected embedding response format: {type(resp)}") from e
            batches.append(np.vstack(vectors))
        return np.vstack(batches) if batches else np.zeros((0, 768), dtype=np.float32)


class GeminiClient:
    def __init__(self, model_name: str, api_key: str):
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set. Please configure your environment.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, max_output_tokens: int = 512) -> str:
        print("[LLM] Prompt to Gemini:\n" + (prompt if len(prompt) < 4000 else prompt[:4000] + "\n... [truncated]"))
        print("[LLM] Generating answer with Gemini…")
        response = self.model.generate_content(prompt, generation_config={"max_output_tokens": max_output_tokens})
        return (response.text or "").strip()

    def summarize(self, text: str, target_ratio: float = 0.2) -> str:
        """Summarize text to approximately target_ratio of original length."""
        prompt = (
            f"Please summarize the following text, reducing it to approximately {int(target_ratio * 100)}% of its original length. "
            f"Keep all important information, key points, and factual details. "
            f"Maintain the structure and organization of the original text.\n\n"
            f"Text to summarize:\n{text}"
        )
        return self.generate(prompt, max_output_tokens=2048)


class RAGPipeline:
    def __init__(self, store: FaissStore, embedder: EmbeddingsClient, llm: GeminiClient):
        self.store = store
        self.embedder = embedder
        self.llm = llm

    def build_index(self, chunks: List[Dict[str, Any]]) -> int:
        texts = [c["text"] for c in chunks]
        metas = chunks
        if not texts:
            return 0
        print(f"[INDEX] Embedding {len(texts)} chunks…")
        vectors = self.embedder.embed(texts)
        print(f"[INDEX] Adding {vectors.shape[0]} vectors to FAISS…")
        self.store.add(vectors, metas)
        self.store.save()
        print("[INDEX] Saved index and metadata.")
        return vectors.shape[0]

    def retrieve(self, question: str, top_k: int) -> List[Dict[str, Any]]:
        print("[RETRIEVE] Embedding question…")
        q_vec = self.embedder.embed([question])[0]
        print(f"[RETRIEVE] Searching top {top_k}…")
        hits = self.store.search(q_vec, top_k)
        results: List[Dict[str, Any]] = []
        for score, meta in hits:
            results.append({
                "score": score,
                "text": meta.get("text", ""),
                "source_file": meta.get("source_file", ""),
                "page_start": int(meta.get("page_start", 0)),
                "page_end": int(meta.get("page_end", 0)),
            })
        print(f"[RETRIEVE] Retrieved {len(results)} chunks.")
        return results

    def answer(self, question: str, top_k: int, max_output_tokens: int) -> Dict[str, Any]:
        retrieved = self.retrieve(question, top_k)
        context_blocks = []
        for i, r in enumerate(retrieved, start=1):
            header = f"[Source {i}] file: {r['source_file']} pages: {r['page_start']}-{r['page_end']} (score={r['score']:.3f})"
            context_blocks.append(header + "\n" + r["text"]) 
        context_text = "\n\n".join(context_blocks)
        prompt = (
            "You are a helpful assistant answering questions about Jharkhand government policies.\n"
            "Use ONLY the provided sources. If the answer is not contained, say you don't know.\n"
            "Cite sources inline as [Source N] where N corresponds to the source block.\n\n"
            f"Question: {question}\n\nSources:\n{context_text}\n\nAnswer:"
        )
        answer_text = self.llm.generate(prompt, max_output_tokens=max_output_tokens)
        citations = []
        for i, r in enumerate(retrieved, start=1):
            citations.append({
                "source_file": r["source_file"],
                "page_start": r["page_start"],
                "page_end": r["page_end"],
                "score": r["score"],
                "snippet": r["text"][:500],
            })
        return {"answer": answer_text, "citations": citations, "prompt": prompt}
