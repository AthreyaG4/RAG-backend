import time
import random
from db import SessionLocal
from llama_cloud_services import LlamaParse
from config import settings
from utils.s3 import read_file_from_s3

LLAMA_PARSE_API_KEY = settings.LLAMA_PARSE_API_KEY

def chunk_document(document):
    db = SessionLocal()

    file_name = document.filename
    file_content = read_file_from_s3(document.s3_key)

    parser_no_llm = LlamaParse(
        api_key=LLAMA_PARSE_API_KEY,
        parse_mode="parse_page_without_llm",
    )

    result = parser_no_llm.parse(file_content, extra_info = {"file_name": file_name})

    parser_lvm = LlamaParse(
        api_key=LLAMA_PARSE_API_KEY,
        parse_mode="parse_page_with_lvm",
        result_type="markdown",
        hide_headers = True,
        hide_footers = True,
        user_prompt=""" For every object image in the page (not screenshots), insert a placeholder using the exact filename.
                        The filenames follow the format img_p{page_number}_{image_number}.png, e.g., img_p0_1.png for the first image on page 0.
                        Do not insert placeholders for screenshots. Keep all other content as normal markdown."""
    )

    result_lvm = parser_lvm.parse(file_content, extra_info = {"file_name": file_name})

    for page in result_lvm.pages:
        print(page.md)

    chunks = [
        {"content" : "This is chunk 1", "type": "text"},
        {"content" : "This is chunk 2", "type": "text,image"},
        {"content" : "This is chunk 3", "type": "text,image,table"},
    ]

    return chunks