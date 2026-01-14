"""
Module 5: RAG System - Retrieval-Augmented Generation
- Chunks code into embeddings using Gemini
- Stores in ChromaDB vector database
- Retrieves relevant code context for questions
- Uses Gemini for intelligent Q&A
"""

import chromadb
import os
from typing import List, Dict, Any
from google.generativeai import GenerativeModel
from colorama import Fore
import json


class CodeRAGSystem:
    """Retrieval-Augmented Generation system for code analysis."""

    def __init__(self):
        """Initialize ChromaDB (new API) and Gemini."""
        # ✅ NEW Chroma client (no deprecated config)
        self.client = chromadb.PersistentClient(path="./chroma_db")

        self.model = GenerativeModel("gemini-2.5-flash")
        self.collection = None

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------
    def create_collection(self, collection_name: str = "erpnext_code"):
        """Create or get ChromaDB collection."""
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"{Fore.GREEN}✓ Collection ready: {collection_name}")

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------
    def chunk_code(
        self, code: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[Dict]:
        """Split code into overlapping chunks."""
        chunks = []
        lines = code.split("\n")

        step = chunk_size - overlap
        for i in range(0, len(lines), step):
            chunk_lines = lines[i : i + chunk_size]
            text = "\n".join(chunk_lines)

            if text.strip():
                chunks.append({
                    "text": text,
                    "start_line": i + 1,
                    "end_line": min(i + chunk_size, len(lines))
                })

        return chunks

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def embed_code_chunks(self, chunks: List[Dict], file_path: str):
        """Add chunks to ChromaDB (Chroma handles embeddings internally)."""
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{file_path}_{idx}_{chunk['start_line']}"

            self.collection.add(
                ids=[chunk_id],
                documents=[chunk["text"]],
                metadatas=[{
                "file": os.path.normpath(file_path).replace("\\", "/"),
                "folder": os.path.normpath(
                os.path.relpath(os.path.dirname(file_path))
                ).replace("\\", "/"),
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "chunk_index": idx
                }]
            )

    def add_file_to_rag(self, file_path: str) -> int:
        """Add a single Python file to RAG."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception as e:
            print(f"{Fore.RED}Error reading {file_path}: {e}")
            return 0

        chunks = self.chunk_code(code)
        self.embed_code_chunks(chunks, file_path)
        return len(chunks)

    def add_folder_to_rag(self, folder_path: str) -> Dict[str, int]:
        """Add all Python files in a folder to RAG."""
        results = {"total_files": 0, "total_chunks": 0}

        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [
                d for d in dirs
                if d not in ["venv", "__pycache__", ".git", "node_modules", ".pytest_cache"]
            ]

            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    rel = os.path.relpath(path, folder_path)

                    chunks = self.add_file_to_rag(path)
                    results["total_files"] += 1
                    results["total_chunks"] += chunks
                    print(f"{Fore.GREEN}✓ {rel} ({chunks} chunks)")

        return results

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------


    def query(
    self,
    question: str,
    n_results: int = 10,
    file: str = None,
    folder: str = None
    ) -> Dict[str, Any]:
        """Retrieve relevant code chunks with optional file/folder filtering."""

        if not self.collection:
            return {"error": "Collection not initialized"}

        # Only exact-match filters allowed in Chroma
        where = {}
        if file:
            file = os.path.normpath(file).replace("\\", "/")
            where["file"] = file

        results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            where=where if where else None
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        # 🔥 Manual folder filtering (CORRECT way)
        if folder:
            folder = os.path.normpath(folder).replace("\\", "/")

            filtered = []
            for d, m, dist in zip(docs, metas, dists):
                meta_folder = os.path.normpath(
                        m.get("folder", "")
                            ).replace("\\", "/")
                if meta_folder.startswith(folder):
                    filtered.append((d, m, dist))

            if not filtered:
                return {"query": question, "chunks": [], "metadata": [], "distances": []}

            docs, metas, dists = zip(*filtered)

        return {
            "query": question,
            "chunks": list(docs),
            "metadata": list(metas),
            "distances": list(dists),
        }


    
        # ------------------------------------------------------------------
    # Keyword Search (RAG-style)
    # ------------------------------------------------------------------
    def search_code(self, keyword: str, n_results: int = 10) -> List[Dict]:
        """Search codebase using vector similarity."""
        results = self.query(keyword, n_results)

        if "error" in results:
            return []

        search_results = []
        for chunk, meta, distance in zip(
            results["chunks"],
            results["metadata"],
            results["distances"]
        ):
            search_results.append({
                "file": meta.get("file"),
                "start_line": meta.get("start_line"),
                "end_line": meta.get("end_line"),
                "code": chunk,
                "similarity": round(1 - distance, 4)
            })

        return search_results


    # ------------------------------------------------------------------
    # RAG Answer
    # ------------------------------------------------------------------

    def ask(self, question: str, file: str = None, folder: str = None) -> str:
        """Ask question with optional file/folder scope."""
        results = self.query(question, file=file, folder=folder)
        if "error" in results:
            return results["error"]

        if not results["chunks"]:
            return "No relevant code found for the given scope."

        context = "=== RELEVANT CODE CONTEXT ===\n\n"
        for chunk, meta in zip(results["chunks"], results["metadata"]):
            context += (
                f"[File: {meta['file']} | "
                f"Lines {meta['start_line']}–{meta['end_line']}]\n"
            )
            context += chunk + "\n\n"

        prompt = f"""
    You are an ERPNext backend expert.

    Use ONLY the context below to answer.

    {context}

    Question:
    {question}

    Give a concise, developer-focused answer.
    """

        response = self.model.generate_content(prompt)
        return response.text if response else "No response generated"


    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def get_db_stats(self) -> Dict[str, Any]:
        if not self.collection:
            return {"error": "Collection not initialized"}

        return {
            "collection": self.collection.name,
            "total_chunks": self.collection.count(),
            "db_path": "./chroma_db"
        }

    # ------------------------------------------------------------------
    # Save Q&A
    # ------------------------------------------------------------------
    def save_query_results(
        self, question: str, answer: str, filename: str = "rag_queries.json"
    ):
        record = {"question": question, "answer": answer}

        data = []
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
            except:
                pass

        data.append(record)
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

