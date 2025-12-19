from fastapi import Depends, APIRouter, HTTPException, status
from schemas import MessageCreateRequest, MessageResponse
from db import get_db
from models import User, Project, Message
from sqlalchemy.orm import Session
from uuid import UUID
from security.jwt import get_current_active_user

route = APIRouter(prefix="/api/projects/{project_id}/messages", tags=["messages"])

@route.get("/", response_model=list[MessageResponse])
async def list_messages(project_id: UUID, 
                        current_user: User = Depends(get_current_active_user), 
                        db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return db.query(Message).filter(Message.project_id == project_id).all()

@route.post("/", response_model=MessageResponse)
async def create_message(project_id: UUID,
                         message: MessageCreateRequest,
                         current_user: User = Depends(get_current_active_user),
                         db: Session = Depends(get_db)):

    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    db_messages = Message(
            role=message.role,
            content=message.content,
            project_id=project_id
        )

    db.add(db_messages)
    db.commit()
    return db_messages