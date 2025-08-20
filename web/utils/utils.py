"""Utilities for the Web UI to interact with backend API services.

This module exposes a thin wrapper around httpx (sync + async) to simplify
calling the FastAPI endpoints used by the Streamlit Web UI. It previously
contained Chinese log / error messages which have been translated to English.
The file was corrupted during a bulk translation step and has been fully
reconstructed here.
"""

from __future__ import annotations

import contextlib
import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Tuple, Union

import httpx

from config.config import Configs
from server.utils.utils import get_httpx_client, api_address
from utils.log_common import build_logger

logger = build_logger()

class ApiRequest:
    """Synchronous helper for calling backend API endpoints.

    Attributes
    ----------
    base_url: str
        Base API address (protocol + host + port).
    timeout: float
        Default timeout passed to httpx client.
    """

    def __init__(
        self,
        base_url: str = api_address(),
        timeout: float = Configs.basic_config.http_default_timeout,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self._use_async = False
        self._client = None

    @property
    def client(self):
        if self._client is None or self._client.is_closed:
            self._client = get_httpx_client(
                base_url=self.base_url, use_async=self._use_async, timeout=self.timeout
            )
        return self._client

    def get(
        self,
        url: str,
        params: Union[Dict, List[Tuple], bytes] = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[httpx.Response, Iterator[httpx.Response], None]:
        while retry > 0:
            try:
                if stream:
                    return self.client.stream("GET", url, params=params, **kwargs)
                else:
                    return self.client.get(url, params=params, **kwargs)
            except Exception as e:
                msg = f"error when get {url}: {e}"
                logger.error(f"{e.__class__.__name__}: {msg}")
                retry -= 1

    def post(
        self,
        url: str,
        data: Dict = None,
        json: Dict = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[httpx.Response, Iterator[httpx.Response], None]:
        while retry > 0:
            try:
                # print(kwargs)
                if stream:
                    return self.client.stream(
                        "POST", url, data=data, json=json, **kwargs
                    )
                else:
                    return self.client.post(url, data=data, json=json, **kwargs)
            except Exception as e:
                msg = f"error when post {url}: {e}"
                logger.error(f"{e.__class__.__name__}: {msg}")
                retry -= 1

    def delete(
        self,
        url: str,
        data: Dict = None,
        json: Dict = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[httpx.Response, Iterator[httpx.Response], None]:
        while retry > 0:
            try:
                if stream:
                    return self.client.stream(
                        "DELETE", url, data=data, json=json, **kwargs
                    )
                else:
                    return self.client.delete(url, data=data, json=json, **kwargs)
            except Exception as e:
                msg = f"error when delete {url}: {e}"
                logger.error(f"{e.__class__.__name__}: {msg}")
                retry -= 1

    def _httpx_stream2generator(
        self,
        response: contextlib._GeneratorContextManager,
        as_json: bool = False,
    ):
        """Convert the httpx.stream context manager into a plain generator.

        Handles SSE style lines that may start with 'data: ' and accumulates
        partial JSON fragments until they parse successfully.
        """

        async def ret_async(response, as_json):  # type: ignore
            try:
                async with response as r:
                    chunk_cache = ""
                    async for chunk in r.aiter_text(None):
                        if not chunk:  # fastchat api yield empty bytes on start and end
                            continue
                        if as_json:
                            try:
                                if chunk.startswith("data: "):
                                    data = json.loads(chunk_cache + chunk[6:-2])
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    data = json.loads(chunk_cache + chunk)
                                # success -> clear cache
                                chunk_cache = ""
                                yield data
                            except Exception as e:
                                msg = f"Interface returned JSON error: '{chunk}'. Error: {e}."
                                logger.error(f"{e.__class__.__name__}: {msg}")
                                if chunk.startswith("data: "):
                                    chunk_cache += chunk[6:-2]
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    chunk_cache += chunk
                                continue
                        else:
                            # print(chunk, end="", flush=True)
                            yield chunk
            except httpx.ConnectError as e:
                msg = f"Unable to connect to API server, please confirm 'api.py' is running. ({e})"
                logger.error(msg)
                yield {"code": 500, "msg": msg}
            except httpx.ReadTimeout as e:
                msg = (
                    "API communication timeout, please ensure FastChat and API services are started "
                    "(see Wiki '5. Start API Service or Web UI'). "
                    f"({e})"
                )
                logger.error(msg)
                yield {"code": 500, "msg": msg}
            except Exception as e:
                msg = f"API communication encountered an error: {e}"
                logger.error(f"{e.__class__.__name__}: {msg}")
                yield {"code": 500, "msg": msg}

        def ret_sync(response, as_json):  # type: ignore
            try:
                with response as r:
                    chunk_cache = ""
                    for chunk in r.iter_text(None):
                        if not chunk:  # fastchat api yield empty bytes on start and end
                            continue
                        if as_json:
                            try:
                                if chunk.startswith("data: "):
                                    data = json.loads(chunk_cache + chunk[6:-2])
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    data = json.loads(chunk_cache + chunk)
                                # success -> clear cache
                                chunk_cache = ""
                                yield data
                            except Exception as e:
                                msg = f"Interface returned JSON error: '{chunk}'. Error: {e}."
                                logger.error(f"{e.__class__.__name__}: {msg}")
                                if chunk.startswith("data: "):
                                    chunk_cache += chunk[6:-2]
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    chunk_cache += chunk
                                continue
                        else:
                            # print(chunk, end="", flush=True)
                            yield chunk
            except httpx.ConnectError as e:
                msg = f"Unable to connect to API server, please confirm 'api.py' is running. ({e})"
                logger.error(msg)
                yield {"code": 500, "msg": msg}
            except httpx.ReadTimeout as e:
                msg = (
                    "API communication timeout, please ensure FastChat and API services are started "
                    "(see Wiki '5. Start API Service or Web UI'). "
                    f"({e})"
                )
                logger.error(msg)
                yield {"code": 500, "msg": msg}
            except Exception as e:
                msg = f"API communication encountered an error: {e}"
                logger.error(f"{e.__class__.__name__}: {msg}")
                yield {"code": 500, "msg": msg}

        if self._use_async:
            return ret_async(response, as_json)
        else:
            return ret_sync(response, as_json)

    def _get_response_value(
        self,
        response: httpx.Response,
        as_json: bool = False,
        value_func: Callable = None,
    ):
        """Normalize sync/async httpx responses.

        Parameters
        ----------
        response: httpx.Response | Awaitable[httpx.Response]
        as_json: bool
            If True, attempt to parse JSON.
        value_func: Callable
            Function applied to response (or parsed JSON) before returning.
        """

        def to_json(r):
            try:
                return r.json()
            except Exception as e:
                msg = "API failed to return valid JSON. " + str(e)
                logger.error(f"{e.__class__.__name__}: {msg}")
                return {"code": 500, "msg": msg, "data": None}

        if value_func is None:
            value_func = lambda r: r

        async def ret_async(response):
            if as_json:
                return value_func(to_json(await response))
            else:
                return value_func(await response)

        if self._use_async:
            return ret_async(response)
        else:
            if as_json:
                return value_func(to_json(response))
            else:
                return value_func(response)


    # Knowledge base operations
    def list_knowledge_bases(self) -> List[str]:
        """List existing knowledge bases."""
        response = self.get("/knowledge_base/list_knowledge_bases")
        return self._get_response_value(
            response, as_json=True, value_func=lambda r: r.get("data", [])
        )

    def create_knowledge_base(
        self,
        knowledge_base_name: str,
        vector_store_type: str = Configs.kb_config.default_vs_type,
        embed_model: str = Configs.llm_config.embedding_models,
    ):
        """Create a new knowledge base."""
        data = {
            "knowledge_base_name": knowledge_base_name,
            "vector_store_type": vector_store_type,
            "embed_model": embed_model,
        }
        response = self.post(
            "/knowledge_base/create_knowledge_base",
            json=data,
        )
        return self._get_response_value(response, as_json=True)

    def delete_knowledge_base(self, knowledge_base_name: str):
        """Delete a knowledge base by name."""
        response = self.post(
            "/knowledge_base/delete_knowledge_base",
            json=f"{knowledge_base_name}",
        )
        return self._get_response_value(response, as_json=True)

    def list_kb_docs(self, knowledge_base_name: str):
        """List documents in a knowledge base."""
        response = self.get(
            "/knowledge_base/list_files",
            params={"knowledge_base_name": knowledge_base_name},
        )
        return self._get_response_value(
            response, as_json=True, value_func=lambda r: r.get("data", [])
        )

    def search_kb_docs(
        self,
        knowledge_base_name: str,
        query: str = "",
        top_k: int = Configs.kb_config.top_k,
        score_threshold: int = Configs.kb_config.score_threshold,
        file_name: str = "",
        metadata: dict = {},
    ) -> List:
        """Semantic search against knowledge base documents."""
        data = {
            "query": query,
            "knowledge_base_name": knowledge_base_name,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "file_name": file_name,
            "metadata": metadata,
        }
        response = self.post(
            "/knowledge_base/search_docs",
            json=data,
        )
        return self._get_response_value(response, as_json=True)

    def upload_kb_docs(
        self,
        files: List[Union[str, Path, bytes]],
        knowledge_base_name: str,
        override: bool = False,
        to_vector_store: bool = True,
        chunk_size=Configs.kb_config.chunk_size,
        chunk_overlap=Configs.kb_config.overlap_size,
        docs: Dict = {},
        not_refresh_vs_cache: bool = False,
    ):
        """Upload (and optionally vectorize) documents to a knowledge base."""

        def convert_file(file, filename=None):
            if isinstance(file, bytes):  # raw bytes
                file = BytesIO(file)
            elif hasattr(file, "read"):  # a file io like object
                filename = filename or file.name
            else:  # a local path
                file = Path(file).absolute().open("rb")
                filename = filename or os.path.split(file.name)[-1]
            return filename, file

        files = [convert_file(file) for file in files]
        data = {
            "knowledge_base_name": knowledge_base_name,
            "override": override,
            "to_vector_store": to_vector_store,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "docs": docs,
            "not_refresh_vs_cache": not_refresh_vs_cache,
        }
        if isinstance(data["docs"], dict):
            data["docs"] = json.dumps(data["docs"], ensure_ascii=False)
        response = self.post(
            "/knowledge_base/upload_docs",
            data=data,
            files=[("files", (filename, file)) for filename, file in files],
        )
        return self._get_response_value(response, as_json=True)

    def delete_kb_docs(
        self,
        knowledge_base_name: str,
        file_names: List[str],
        delete_content: bool = False,
        not_refresh_vs_cache: bool = False,
    ):
        """Delete documents (and optionally underlying content) from a knowledge base."""
        data = {
            "knowledge_base_name": knowledge_base_name,
            "file_names": file_names,
            "delete_content": delete_content,
            "not_refresh_vs_cache": not_refresh_vs_cache,
        }
        response = self.post(
            "/knowledge_base/delete_docs",
            json=data,
        )
        return self._get_response_value(response, as_json=True)

    def update_kb_info(self, knowledge_base_name: str, kb_info: Dict[str, Any]):
        """Update metadata / info for a knowledge base."""
        data = {"knowledge_base_name": knowledge_base_name, "kb_info": kb_info}
        response = self.post(
            "/knowledge_base/update_info",
            json=data,
        )
        return self._get_response_value(response, as_json=True)

    def update_kb_docs(
        self,
        knowledge_base_name: str,
        file_names: List[str],
        override_custom_docs: bool = False,
        chunk_size=Configs.kb_config.chunk_size,
        chunk_overlap=Configs.kb_config.overlap_size,
        docs: Dict = {},
        not_refresh_vs_cache: bool = False,
    ):
        """Re-chunk or re-vectorize existing documents in a knowledge base."""
        data = {
            "knowledge_base_name": knowledge_base_name,
            "file_names": file_names,
            "override_custom_docs": override_custom_docs,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "docs": docs,
            "not_refresh_vs_cache": not_refresh_vs_cache,
        }
        if isinstance(data["docs"], dict):
            data["docs"] = json.dumps(data["docs"], ensure_ascii=False)
        response = self.post(
            "/knowledge_base/update_docs",
            json=data,
        )
        return self._get_response_value(response, as_json=True)



class AsyncApiRequest(ApiRequest):
    """Asynchronous variant of ApiRequest."""

    def __init__(
        self,
        base_url: str = api_address(),
        timeout: float = Configs.basic_config.http_default_timeout,
    ):
        super().__init__(base_url, timeout)
        self._use_async = True


def check_error_msg(data: Union[str, dict, list], key: str = "errorMsg") -> str:
    """Return error message if an error occurred when requesting the API."""
    if isinstance(data, dict):
        if key in data:
            return data[key]
        if "code" in data and data["code"] != 200:
            return data["msg"]
    return ""


def check_success_msg(data: Union[str, dict, list], key: str = "msg") -> str:
    """Return success message (msg field) if present and code == 200."""
    if (
        isinstance(data, dict)
        and key in data
        and "code" in data
        and data["code"] == 200
    ):
        return data[key]
    return ""



def webui_address() -> str:
    """Return configured Web UI base address."""
    host = Configs.basic_config.webui_server["host"]
    port = Configs.basic_config.webui_server["port"]
    return f"http://{host}:{port}"
