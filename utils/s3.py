import boto3
from botocore.exceptions import ClientError
from config import settings
import os
from datetime import datetime
import uuid
from typing import List
from fastapi import UploadFile
from uuid import UUID

S3_BUCKET = settings.S3_BUCKET_NAME
AWS_REGION = settings.AWS_REGION

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

async def read_file_from_s3(s3_key: str) -> bytes:
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
    return response['Body'].read()

async def upload_files_to_s3(user_id: UUID, project_id: UUID, files: List[UploadFile]):
    allowed_extensions = {".pdf", ".txt", ".md", ".doc", ".docx"}

    results = []
    total_size = 0

    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower() # type: ignore
        if file_ext not in allowed_extensions:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": f"File type {file_ext} not allowed"
            })
            continue
        unique_id = str(uuid.uuid4())[:8]
        original_name = os.path.splitext(file.filename)[0] #type: ignore
        s3_key = f"uploads/{user_id}/{project_id}/{unique_id}_{original_name}{file_ext}"

        try:
            file_content = await file.read()
            file_size = len(file_content)
            
            # Upload to S3
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or "application/octet-stream",
                Metadata={
                    'original_filename': file.filename,
                    'uploaded_at': datetime.now().isoformat()
                }
            )
            
            file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
            
            results.append({
                "filename": file.filename,
                "status": "uploaded",
                "s3_key": s3_key,
                "file_url": file_url,
                "size": file_size
            })
            
            total_size += file_size
            
        except ClientError as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"S3 upload failed: {str(e)}"
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"Upload failed: {str(e)}"
            })

    successful = sum(1 for r in results if r["status"] == "uploaded")
    failed = len(results) - successful

    return {
        "results": results,
        "total_size": total_size,
        "successful_count": successful,
        "failed_count": failed
    }

async def delete_file_from_s3(s3_key: str):
    if not s3_key:
        return
    
    try:
        s3_response = s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        return True
    except Exception as e:
        raise Exception(f"Failed to delete {s3_key} from S3: {str(e)}")
