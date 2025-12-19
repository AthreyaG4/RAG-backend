from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import List

class UserCreateRequest(BaseModel):
    name: str
    username: str
    password: str
    email: EmailStr

class JWTToken(BaseModel):
    access_token: str
    token_type: str

class ProjectCreateRequest(BaseModel):
    name: str

class DocumentCreateRequest(BaseModel):
    filename: str

class ChunkCreateRequest(BaseModel):
    content: str

class MessageCreateRequest(BaseModel):
    role: str
    content: str

class ProjectUpdateRequest(BaseModel):
    name: str | None = None

class UserResponse(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    created_at: datetime
    projects: List["ProjectResponse"] = []

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    status: str
    created_at: datetime
    documents: List["DocumentResponse"] = []
    messages: List["MessageResponse"] = []

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    created_at: datetime
    status: str = "uploaded"
    chunks: List["ChunkResponse"] = []

    class Config:
        from_attributes = True

class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: UUID
    project_id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True