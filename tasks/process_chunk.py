from celery_app import celery_app
from db import SessionLocal
from models import Document, Chunk, Project, Image
from uuid import UUID
import requests
from config import settings
from utils.s3 import get_presigned_urls_for_chunk_images

HF_ACCESS_TOKEN = settings.HF_ACCESS_TOKEN
GPU_SERVICE_URL = settings.GPU_SERVICE_URL


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 3},
)
def process_chunk(self, chunk_id: str):
    db = SessionLocal()

    summarized_text = ""
    try:
        chunk_uuid = UUID(chunk_id)

        chunk = db.query(Chunk).filter(Chunk.id == chunk_uuid).with_for_update().first()

        if not chunk:
            return {"status": "error", "message": "Chunk not found"}

        if chunk.status == "embedded":
            return {"status": "already_processed"}

        document = (
            db.query(Document)
            .filter(Document.id == chunk.document_id)
            .with_for_update()
            .first()
        )

        images = db.query(Image).filter(Image.chunk_id == chunk.id).all()

        if len(images) != 0:
            image_urls = get_presigned_urls_for_chunk_images(
                images=images,
                expires_in=900,
            )

            summarize_resp = requests.post(
                f"{GPU_SERVICE_URL}/summarize",
                headers={"Authorization": f"Bearer {HF_ACCESS_TOKEN}"},
                json={
                    "chunk_text": chunk.content,
                    "image_urls": image_urls,
                },
                timeout=500,
            )
            summarize_resp.raise_for_status()

            summarized_text = summarize_resp.json()["summary_text"]
            chunk.summarised_content = summarized_text
        else:
            chunk.summarised_content = chunk.content
            summarized_text = chunk.content

        chunk.status = "summarized"
        document.chunks_summarized += 1

        embed_resp = requests.post(
            f"{GPU_SERVICE_URL}/embed",
            headers={"Authorization": f"Bearer {HF_ACCESS_TOKEN}"},
            json={"summarized_text": summarized_text},
            timeout=100,
        )
        embed_resp.raise_for_status()

        embedding = embed_resp.json()["embedding_vector"]

        chunk.embedding = embedding
        chunk.status = "embedded"
        document.chunks_embedded += 1

        if document.chunks_embedded == document.total_chunks:
            document.status = "ready"

            project = (
                db.query(Project)
                .filter(Project.id == document.project_id)
                .with_for_update()
                .first()
            )

            all_docs = (
                db.query(Document).filter(Document.project_id == project.id).all()
            )

            if all(
                d.status == "ready" and d.chunks_embedded == d.total_chunks
                for d in all_docs
            ):
                project.status = "ready"

        db.commit()
        return {"status": "done"}

    except Exception as e:
        db.rollback()

        chunk = db.query(Chunk).filter(Chunk.id == chunk_uuid).first()
        if chunk:
            chunk.status = "failed"
            document = (
                db.query(Document).filter(Document.id == chunk.document_id).first()
            )
            if document:
                document.status = "failed"
            db.commit()

        raise

    finally:
        db.close()
