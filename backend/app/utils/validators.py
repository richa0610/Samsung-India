from fastapi import UploadFile

from app.core.exceptions import bad_request
from app.core.media import (
    ALLOWED_DOCUMENT_CONTENT_TYPES,
    ALLOWED_PHOTO_CONTENT_TYPES,
    FILE_SIGNATURES,
    MAX_UPLOAD_BYTES,
)


async def _read_upload(
    file: UploadFile,
    allowed: dict[str, str],
    *,
    type_error: str,
    size_error_detail: str,
) -> tuple[bytes, str]:
    """Reads an upload and returns (contents, file extension) once it is one of `allowed`'s types -
    by the type the client declares AND by the file's own first bytes - and at most 5MB. Never
    reads more than one byte past the limit, so an oversized upload can't fill the server's memory."""
    content_type = file.content_type or ""
    extension = allowed.get(content_type)
    if not extension:
        raise bad_request(type_error)

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise bad_request(size_error_detail)
    if not contents.startswith(FILE_SIGNATURES[content_type]):
        raise bad_request(type_error)

    return contents, extension


async def read_photo_upload(file: UploadFile, *, size_error_detail: str) -> tuple[bytes, str]:
    """A photo: profile picture, check-in or training start/end photo - JPEG only."""
    return await _read_upload(
        file, ALLOWED_PHOTO_CONTENT_TYPES,
        type_error="Only JPG photos are allowed",
        size_error_detail=size_error_detail,
    )


async def read_document_upload(file: UploadFile, *, size_error_detail: str) -> tuple[bytes, str]:
    """A document: the Aadhaar card or the signed attendance sheet - JPEG or PDF."""
    return await _read_upload(
        file, ALLOWED_DOCUMENT_CONTENT_TYPES,
        type_error="Only JPG or PDF files are allowed",
        size_error_detail=size_error_detail,
    )
