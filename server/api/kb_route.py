from __future__ import annotations

from typing import List

from fastapi import APIRouter
from rag.kb.api.kb_api import create_kb, delete_kb, list_kbs
from rag.kb.api.kb_doc_api import (
    delete_docs,
    list_files,
    search_docs,
    update_info,
    upload_docs, download_doc, update_docs,
)
from server.utils.utils import ListResponse, BaseResponse

kb_router = APIRouter(prefix="/knowledge_base", tags=["Knowledge Base Management"])



kb_router.get(
    "/list_knowledge_bases", response_model=ListResponse, summary="Get knowledge base list"
)(list_kbs)

kb_router.post(
    "/create_knowledge_base", response_model=BaseResponse, summary="Create knowledge base"
)(create_kb)

kb_router.post(
    "/delete_knowledge_base", response_model=BaseResponse, summary="Delete knowledge base"
)(delete_kb)

kb_router.get(
    "/list_files", response_model=ListResponse, summary="Get file list in knowledge base"
)(list_files)

kb_router.post("/search_docs", response_model=List[dict], summary="Search knowledge base")(
    search_docs
)

kb_router.post(
    "/upload_docs",
    response_model=BaseResponse,
    summary="Upload files to knowledge base and/or vectorize",
)(upload_docs)

kb_router.post(
    "/delete_docs", response_model=BaseResponse, summary="Delete specified files in knowledge base"
)(delete_docs)

kb_router.post("/update_info", response_model=BaseResponse, summary="Update knowledge base description")(
    update_info
)

kb_router.post(
    "/update_docs", response_model=BaseResponse, summary="Update existing files to knowledge base"
)(update_docs)

kb_router.get("/download_doc", summary="Download corresponding knowledge file")(download_doc)




