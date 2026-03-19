from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
from app.models.document import DocumentStatus, DOCUMENTS_COLLECTION
from app.models.embedding import EMBEDDINGS_COLLECTION
from app.core.database import serialize_doc
import PyPDF2
import docx


class RAGService:
    """Service for Retrieval Augmented Generation operations"""

    def __init__(self):
        self.embedding_model: Optional[SentenceTransformer] = None
        self.embeddings_available = True
        self.chunk_size = 500
        self.chunk_overlap = 50

    def _get_embedding_model(self) -> Optional[SentenceTransformer]:
        """Lazily initialize embedding model to prevent startup-time network failures."""
        if not self.embeddings_available:
            return None

        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                self.embeddings_available = False
                return None

        return self.embedding_model

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > self.chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]

    async def process_document(
        self,
        document_id: str,
        file_path: str,
        db: AsyncIOMotorDatabase
    ):
        """Process document and create embeddings"""
        from bson import ObjectId
        doc = await db[DOCUMENTS_COLLECTION].find_one({"_id": ObjectId(document_id)})
        if not doc:
            return

        try:
            file_type = doc["file_type"]
            if file_type == "pdf":
                text = self.extract_text_from_pdf(file_path)
            elif file_type in ["docx", "doc"]:
                text = self.extract_text_from_docx(file_path)
            elif file_type == "txt":
                text = self.extract_text_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            chunks = self.chunk_text(text)

            embedding_model = self._get_embedding_model()
            if embedding_model is None:
                await db[DOCUMENTS_COLLECTION].update_one(
                    {"_id": ObjectId(document_id)},
                    {"$set": {"status": DocumentStatus.FAILED.value}}
                )
                return

            embedding_docs = []
            for idx, chunk in enumerate(chunks):
                embedding_vector = embedding_model.encode(chunk).tolist()
                embedding_docs.append({
                    "document_id": document_id,
                    "chatbot_id": doc["chatbot_id"],
                    "chunk_text": chunk,
                    "chunk_index": idx,
                    "embedding": embedding_vector,
                    "extra_metadata": {"chunk_length": len(chunk)}
                })

            if embedding_docs:
                await db[EMBEDDINGS_COLLECTION].insert_many(embedding_docs)

            await db[DOCUMENTS_COLLECTION].update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {
                    "status": DocumentStatus.COMPLETED.value,
                    "processed_at": datetime.utcnow()
                }}
            )

        except Exception:
            await db[DOCUMENTS_COLLECTION].update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"status": DocumentStatus.FAILED.value}}
            )

    async def search_similar_chunks(
        self,
        query: str,
        chatbot_id: str,
        db: AsyncIOMotorDatabase,
        top_k: int = 3
    ) -> List[Dict]:
        """Search for similar chunks using cosine similarity"""
        embedding_model = self._get_embedding_model()
        if embedding_model is None:
            return []

        query_embedding = embedding_model.encode(query).tolist()

        cursor = db[EMBEDDINGS_COLLECTION].find({"chatbot_id": chatbot_id})
        embeddings = await cursor.to_list(length=None)

        if not embeddings:
            return []

        results = []
        for emb in embeddings:
            if emb.get("embedding"):
                similarity = self._cosine_similarity(query_embedding, emb["embedding"])
                results.append({
                    "chunk_text": emb["chunk_text"],
                    "similarity": similarity,
                    "chunk_index": emb["chunk_index"]
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a = np.array(vec1)
        b = np.array(vec2)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(np.dot(a, b) / norm)

    def format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into context string"""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Source {i}]:\n{chunk['chunk_text']}")
        return "Relevant information:\n\n" + "\n\n".join(context_parts)
