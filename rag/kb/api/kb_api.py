import urllib

from fastapi import Body

from rag.kb.base import KBServiceFactory
from rag.kb.repository.kb_repository import list_kbs_from_db
from rag.kb.utils.kb_utils import validate_kb_name
from server.utils.utils import ListResponse, BaseResponse


def list_kbs():
    # Get List of Knowledge Base
    return ListResponse(data=list_kbs_from_db())


def create_kb(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        vector_store_type: str = Body(),
        kb_info: str = Body("", description="知识库内容简介，用于Agent选择知识库。"),
        embed_model: str = Body(),
) -> BaseResponse:
    # Create selected knowledge base
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    if knowledge_base_name is None or knowledge_base_name.strip() == "":
        return BaseResponse(code=404, msg="知识库名称不能为空，请重新填写知识库名称")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is not None:
        return BaseResponse(code=404, msg=f"已存在同名知识库 {knowledge_base_name}")

    kb = KBServiceFactory.get_service(
        knowledge_base_name, vector_store_type, embed_model, kb_info=kb_info
    )
    try:
        kb.create_kb()
    except Exception as e:
        msg = f"Error creating knowledge base: {e}"
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=200, msg=f"Knowledge base {knowledge_base_name} has been added")


def delete_kb(
        knowledge_base_name: str = Body(..., examples=["samples"]),
) -> BaseResponse:
    # Delete selected knowledge base
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)

    if kb is None:
        return BaseResponse(code=404, msg=f"Knowledge base {knowledge_base_name} not found")

    try:
        status = kb.clear_vs()
        status = kb.drop_kb()
        if status:
            return BaseResponse(code=200, msg=f"Successfully deleted knowledge base {knowledge_base_name}")
    except Exception as e:
        msg = f"Unexpected error while deleting knowledge base: {e}"
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=500, msg=f"Failed to delete knowledge base {knowledge_base_name}")
