"""Files resource — /v1/files endpoints for batch workflows."""

from __future__ import annotations

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import FileObject, UploadBatchFileParams


class FilesResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def upload(self, params: UploadBatchFileParams) -> FileObject:
        data = self._http.post("/v1/files", params.model_dump(exclude_none=True))
        return FileObject.model_validate(data)

    def get(self, file_id: str) -> FileObject:
        data = self._http.get(f"/v1/files/{file_id}")
        return FileObject.model_validate(data)

    def delete(self, file_id: str) -> None:
        self._http.delete(f"/v1/files/{file_id}")

    def content(self, file_id: str) -> bytes:
        return self._http.get_bytes(f"/v1/files/{file_id}/content")


class AsyncFilesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def upload(self, params: UploadBatchFileParams) -> FileObject:
        data = await self._http.post("/v1/files", params.model_dump(exclude_none=True))
        return FileObject.model_validate(data)

    async def get(self, file_id: str) -> FileObject:
        data = await self._http.get(f"/v1/files/{file_id}")
        return FileObject.model_validate(data)

    async def delete(self, file_id: str) -> None:
        await self._http.delete(f"/v1/files/{file_id}")

    async def content(self, file_id: str) -> bytes:
        return await self._http.get_bytes(f"/v1/files/{file_id}/content")
