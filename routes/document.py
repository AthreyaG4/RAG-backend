from fastapi import Depends, APIRouter, HTTPException, status
from schemas import DocumentCreateRequest, DocumentResponse
from db import get_db
from models import User, Project, Document
from sqlalchemy.orm import Session
from uuid import UUID
from security.jwt import get_current_active_user

route = APIRouter(prefix="/api/projects/{project_id}/documents", tags=["documents"])

@route.get("/", response_model=list[DocumentResponse])
async def list_documents(project_id: UUID, 
                         current_user: User = Depends(get_current_active_user),
                         db: Session = Depends(get_db)):
    
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return db.query(Document).filter(Document.project_id == project_id).all()

@route.get("/{document_id}", response_model=DocumentResponse)
async def get_document(project_id: UUID,
                       document_id: UUID,
                       current_user: User = Depends(get_current_active_user),
                       db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    document = db.query(Document).filter(Document.project_id == project_id,
                                         Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document

@route.post("/", response_model=list[DocumentResponse])
async def create_documents(project_id: UUID,
                           documents: list[DocumentCreateRequest],
                           current_user: User = Depends(get_current_active_user),
                           db: Session = Depends(get_db)):
    
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    db_documents = [
        Document(
            filename=document.filename,
            project_id=project_id
        )
        for document in documents
    ]
    db.add_all(db_documents)
    db.commit()
    for doc in db_documents:
       db.refresh(doc)
    return db_documents