from celery_app import celery_app
from db import SessionLocal
from models import Document, Chunk
from uuid import UUID
from utils.parse import chunk_document
from tasks.process_chunk import process_chunk

@celery_app.task(bind=True)
def process_document(self, project_id: str, document_id: str):
    db = SessionLocal()
    try:
        doc_uuid = UUID(document_id)
        document = db.query(Document).filter(Document.id == doc_uuid).first()

        if not document:
            return {"status": "error", "message": "Document not found"}

        document.status = "chunking" # type: ignore
        db.commit()

        chunks = chunk_document(document) # type: ignore

        for chunk in chunks:
            new_chunk = Chunk(
                document_id=document.id,
                content=chunk['content'],
            )

            types = chunk['type'].split(',')
            new_chunk.has_text = 'text' in types # type: ignore
            new_chunk.has_image = 'image' in types # type: ignore
            new_chunk.has_table = 'table' in types # type: ignore

            db.add(new_chunk)

        document.total_chunks = len(chunks) # type: ignore
        document.status = "processing" # type: ignore
        db.commit()

        # for chunk in db.query(Chunk).filter(Chunk.document_id == document.id).all():
        #     process_chunk.delay(str(chunk.id)) # type: ignore

        return {"status": "done"}
        
    finally:
        db.close()