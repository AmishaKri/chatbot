from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from datetime import datetime
import os
import aiofiles
from app.core.database import get_db, to_object_id, serialize_doc
from app.core.dependencies import get_current_active_user
from app.core.config import settings
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.models.document import DocumentStatus, DOCUMENTS_COLLECTION
from app.models.chatbot import CHATBOTS_COLLECTION
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])
rag_service = RAGService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    chatbot_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Upload a document for knowledge base"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["pdf", "docx", "doc", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Supported: PDF, DOCX, TXT"
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{chatbot_id}_{file.filename}")

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    now = datetime.utcnow()
    doc_record = {
        "chatbot_id": chatbot_id,
        "organization_id": current_user["organization_id"],
        "filename": file.filename,
        "file_type": file_extension,
        "file_size": len(content),
        "file_path": file_path,
        "status": DocumentStatus.PROCESSING.value,
        "uploaded_at": now,
        "processed_at": None
    }
    result = await db[DOCUMENTS_COLLECTION].insert_one(doc_record)
    doc_id = str(result.inserted_id)

    background_tasks.add_task(rag_service.process_document, doc_id, file_path, db)

    return {
        "id": doc_id,
        "filename": file.filename,
        "status": DocumentStatus.PROCESSING.value,
        "message": "Document uploaded and processing started"
    }


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    chatbot_id: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all documents"""
    query: dict = {"organization_id": current_user["organization_id"]}
    if chatbot_id:
        query["chatbot_id"] = chatbot_id

    cursor = db[DOCUMENTS_COLLECTION].find(query).sort("uploaded_at", -1)
    documents = await cursor.to_list(length=None)
    return [serialize_doc(d) for d in documents]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a document"""
    oid = to_object_id(document_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document = await db[DOCUMENTS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if os.path.exists(document["file_path"]):
        os.remove(document["file_path"])

    await db[DOCUMENTS_COLLECTION].delete_one({"_id": oid})
    return {"message": "Document deleted successfully"}


@router.get("/documents/{document_id}/status", response_model=DocumentResponse)
async def get_document_status(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get document processing status"""
    oid = to_object_id(document_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document = await db[DOCUMENTS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return serialize_doc(document)
