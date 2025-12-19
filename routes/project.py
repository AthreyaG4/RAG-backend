from fastapi import Depends, APIRouter, HTTPException, status
from schemas import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from db import get_db
from models import Project, User
from sqlalchemy.orm import Session
from uuid import UUID
from security.jwt import get_current_active_user

route = APIRouter(prefix="/api/projects", tags=["projects"])

@route.get("/", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Project).filter(Project.user_id == current_user.id).all()

@route.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@route.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_project = Project(
        name=project.name,
        user_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@route.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID,
                         project_update: ProjectUpdateRequest,
                         current_user: User = Depends(get_current_active_user),
                         db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    if project_update.name is not None:
        project.name = project_update.name # type: ignore

    db.commit()
    db.refresh(project)
    return project

@route.delete("/{project_id}")
async def delete_project(project_id: UUID,
                         current_user: User = Depends(get_current_active_user),
                         db: Session = Depends(get_db)):
    
    project = db.query(Project).filter(Project.user_id == current_user.id, Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    db.delete(project)
    db.commit()
    return {"detail": "Project deleted successfully"}