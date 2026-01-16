import time
import random
from db import SessionLocal
from llama_cloud_services import LlamaParse

def chunk_document(document):
    db = SessionLocal()

    time.sleep(random.uniform(1,5))

    chunks = [
        {"content" : "This is chunk 1", "type": "text"},
        {"content" : "This is chunk 2", "type": "text,image"},
        {"content" : "This is chunk 3", "type": "text,image,table"},
    ]

    return chunks