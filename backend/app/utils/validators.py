from app.core.exceptions import bad_request
from app.core.media import (
    ALLOWED_DOCUMENT_CONTENT_TYPES,
    ALLOWED_IMAGE_CONTENT_TYPES,
    MAX_UPLOAD_BYTES,
)


def validate_image_upload(content_type: str | None, contents: bytes, *, size_error_detail: str) -> str:
    """Shared JPEG/PNG/WEBP content-type + 5MB size check used by every
    photo-upload endpoint (trainee profile photo, secure check-in photo).
    Returns the file extension to save with. `size_error_detail` lets each
    call site keep its own wording (e.g. "Photo" vs "Image")."""
    extension = ALLOWED_IMAGE_CONTENT_TYPES.get(content_type or "")
    if not extension:
        raise bad_request("Only JPEG, PNG or WEBP images are allowed")

    if len(contents) > MAX_UPLOAD_BYTES:
        raise bad_request(size_error_detail)

    return extension


def validate_document_upload(content_type: str | None, contents: bytes, *, size_error_detail: str) -> str:
    """PDF or image (JPEG/PNG/WEBP) + 5MB check for the attendance-sheet upload
    at session check-out. Returns the extension to save with."""
    extension = ALLOWED_DOCUMENT_CONTENT_TYPES.get(content_type or "")
    if not extension:
        raise bad_request("Attendance sheet must be a PDF or an image (JPEG/PNG/WEBP)")

    if len(contents) > MAX_UPLOAD_BYTES:
        raise bad_request(size_error_detail)

    return extension
