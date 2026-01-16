from celery_app import celery_app
from db import SessionLocal
from models import Document, Chunk, Project
from uuid import UUID
import requests
from config import settings

HF_ACCESS_TOKEN = settings.HF_ACCESS_TOKEN
GPU_SERVICE_URL = settings.GPU_SERVICE_URL

@celery_app.task(bind=True)
def process_chunk(self, chunk_id: str):
    db = SessionLocal()
    try:
        chunk_uuid = UUID(chunk_id)
        chunk = db.query(Chunk).filter(Chunk.id == chunk_uuid).first()

        if not chunk:
            return {"status": "error", "message": "Chunk not found"}

        # Summarize
        summarized_content = requests.post(
            f"{GPU_SERVICE_URL}/summarize",
            headers={
                "Authorization": f"Bearer {HF_ACCESS_TOKEN}"
            },
            data = {
                "chunk_text": chunk.content,
                "image_urls": [
                    "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
                ]
            },
            timeout = 500
        )

        chunk.summarised_content = summarized_content
        chunk.status = "summarized"
        db.commit()

        # Increment document counter
        document = db.query(Document).filter(Document.id == chunk.document_id).first()
        document.chunks_summarized += 1
        db.commit()

        # Embed
        embedding = requests.post(
            f"{GPU_SERVICE_URL}/embed",
            headers={
                "Authorization": f"Bearer {HF_ACCESS_TOKEN}"
            },
            data = {
                "summarized_text" : chunk.summarised_content
            },
            timeout = 100
        )

        chunk.embedding = embedding
        chunk.status = "embedded"
        db.commit()

        # Increment embedded counter
        document = db.query(Document).filter(Document.id == chunk.document_id).first()
        document.chunks_embedded += 1
        db.commit()

        # Refresh document to get updated counts
        document = db.query(Document).filter(Document.id == chunk.document_id).first()
        
        # Check if ALL chunks for THIS document are done
        if document.chunks_embedded == document.total_chunks:
            document.status = "ready"
            db.commit()
            print(f"Document {document.filename} completed!")
            
            # Now check if ALL documents for THIS project are done
            project = db.query(Project).filter(Project.id == document.project_id).first()
            all_documents = db.query(Document).filter(Document.project_id == project.id).all()
            
            all_documents_ready = all(
                doc.status == "ready" and doc.total_chunks and doc.chunks_embedded == doc.total_chunks
                for doc in all_documents
            )
            
            if all_documents_ready:
                project.status = "ready"
                db.commit()
                print(f"Project {project.name} is fully ready!")

        return {"status": "done"}

    except Exception as e:
        print(f"Error processing chunk {chunk_id}: {str(e)}")
        chunk = db.query(Chunk).filter(Chunk.id == chunk_uuid).first()
        if chunk:
            chunk.status = "failed"
            document = db.query(Document).filter(Document.id == chunk.document_id).first()
            if document:
                document.status = "failed"
            db.commit()
        raise

    finally:
        db.close()