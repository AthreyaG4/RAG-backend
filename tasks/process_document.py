from celery_app import celery_app
from db import SessionLocal
from models import Document, Chunk, Image, Project
from uuid import UUID
from utils.parse import chunk_document
from tasks.process_chunk import process_chunk
from utils.s3 import upload_image_to_s3


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 3},
)
def process_document(self, project_id: str, document_id: str):
    db = SessionLocal()

    try:
        doc_uuid = UUID(document_id)
        project_uuid = UUID(project_id)

        document = (
            db.query(Document).filter(Document.id == doc_uuid).with_for_update().first()
        )

        if not document:
            return {"status": "error", "message": "Document not found"}

        if document.status not in ("uploaded", "failed"):
            return {"status": "already_processing"}

        project = db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            return {"status": "error", "message": "Project not found"}

        document.status = "chunking"
        db.commit()

        chunks = chunk_document(document)

        for chunk in chunks:
            new_chunk = Chunk(
                document_id=document.id,
                content=chunk["content"],
                page_number=chunk["page_number"],
                has_text="text" in chunk["type"],
                has_image="image" in chunk["type"],
                has_table="table" in chunk["type"],
            )

            db.add(new_chunk)
            db.flush()

            for image_path in chunk.get("images", []):
                upload_result = upload_image_to_s3(
                    image_path=image_path,
                    user_id=project.user_id,
                    project_id=project_uuid,
                    document_id=doc_uuid,
                    chunk_id=new_chunk.id,
                    page_number=new_chunk.page_number,
                )

                if upload_result["status"] != "uploaded":
                    raise RuntimeError(
                        f"Image upload failed: {upload_result.get('error')}"
                    )

                db.add(
                    Image(
                        chunk_id=new_chunk.id,
                        s3_key=upload_result.get("s3_key"),
                    )
                )

        document.total_chunks = len(chunks)
        document.chunks_summarized = 0
        document.chunks_embedded = 0
        document.status = "processing"

        db.commit()

        for chunk in db.query(Chunk).filter(Chunk.document_id == document.id).all():
            process_chunk.delay(str(chunk.id))

        return {"status": "success", "message": "Chunks created and queued"}

    except Exception as e:
        db.rollback()
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if document:
            document.status = "failed"
            db.commit()
        raise

    finally:
        db.close()
