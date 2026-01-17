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

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    status: str
    created_at: datetime
    messages: List["MessageResponse"] = []

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    created_at: datetime
    status: str
    s3_key: str | None = None
    chunks: List["ChunkResponse"] = []

    class Config:
        from_attributes = True


class DocumentProgressResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    status: str
    total_chunks: int | None
    chunks_summarized: int
    chunks_embedded: int

    class Config:
        from_attributes = True


class ProjectProgressResponse(BaseModel):
    status: str
    total_documents: int
    documents_processed: int
    documents: List[DocumentProgressResponse]


class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    summarised_content: str | None = None
    has_text: bool | None = None
    has_image: bool | None = None
    has_table: bool | None = None
    created_at: datetime
    images: List["ImageResponse"] = []

    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    id: UUID
    chunk_id: UUID
    s3_key: str | None = None
    created_at: datetime


class MessageResponse(BaseModel):
    id: UUID
    project_id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
