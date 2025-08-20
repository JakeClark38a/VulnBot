from fastapi import FastAPI

from server.api.kb_route import kb_router
from config.config import Configs


def create_app():
    app = FastAPI(title="Server")

    # Register knowledge base routes only if enabled
    if Configs.basic_config.enable_knowledge_base:
        app.include_router(kb_router)

    return app

