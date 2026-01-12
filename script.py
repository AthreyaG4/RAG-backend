from fastapi import FastAPI
from db import init_db
from routes.user import route as user_route
from routes.project import route as project_route
from routes.document import route as document_route
from routes.documentChunks import route as chunk_route
from routes.auth import route as login_route
from routes.messages import route as messages_route
from fastapi.middleware.cors import CORSMiddleware

import logging

logging.basicConfig(
    level=logging.INFO,
    format=f'%(asctime)s - RAG Service - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(login_route)
app.include_router(user_route)
app.include_router(project_route)
app.include_router(document_route)
app.include_router(chunk_route)
app.include_router(messages_route)