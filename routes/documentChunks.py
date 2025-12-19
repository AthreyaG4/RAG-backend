from fastapi import Depends, APIRouter, HTTPException, status
from schemas import ChunkCreateRequest, ChunkResponse
from db import get_db
from models import User, Document, Chunk
from sqlalchemy.orm import Session
from uuid import UUID
from security.jwt import get_current_active_user

route = APIRouter(prefix="/api/projects/{project_id}/documents/{document_id}/chunks", tags=["chunks"])

@route.get("/", response_model=list[ChunkResponse])
async def list_chunks(project_id: UUID,
                      document_id: UUID,
                      current_user: User = Depends(get_current_active_user), 
                      db: Session = Depends(get_db)):
    
    document = db.query(Document).join(Document.project).filter(
        Document.id == document_id,
        Document.project_id == project_id,
        Document.project.has(user_id=current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
    return chunks

@route.get("/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(project_id: UUID,
                    document_id: UUID,
                    chunk_id: UUID,
                    current_user: User = Depends(get_current_active_user),
                    db: Session = Depends(get_db)):
    document = db.query(Document).join(Document.project).filter(
        Document.id == document_id,
        Document.project_id == project_id,
        Document.project.has(user_id=current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    chunk = db.query(Chunk).filter(Chunk.document_id == document_id,
                                      Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return chunk

@route.post("/", response_model=list[ChunkResponse])
async def create_chunks(project_id: UUID,
                        document_id: UUID,
                        chunks: list[ChunkCreateRequest],
                        current_user: User = Depends(get_current_active_user),
                        db: Session = Depends(get_db)):
    
    document = db.query(Document).join(Document.project).filter(
        Document.id == document_id,
        Document.project_id == project_id,
        Document.project.has(user_id=current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    db_chunks = [
        Chunk(
            content=chunk.content,
            document_id=document_id
        )
        for chunk in chunks
    ]
    db.add_all(db_chunks)
    db.commit()
    for db_chunk in db_chunks:
        db.refresh(db_chunk)
    return db_chunks