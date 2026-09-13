from app.core.exceptions import bad_request
from app.core.media import (
    ALLOWED_AADHAR_CONTENT_TYPES,
    ALLOWED_DOCUMENT_CONTENT_TYPES,
    ALLOWED_IMAGE_CONTENT_TYPES,
    ALLOWED_PROFILE_PHOTO_CONTENT_TYPES,
    MAX_UPLOAD_BYTES,
)


def _validate_upload(
    content_type: str | None,
    contents: bytes,
    allowed: dict[str, str],
    *,
    type_error: str,
    size_error_detail: str,
) -> str:
    extension = allowed.get(content_type or "")
    if not extension:
        raise bad_request(type_error)

    if len(contents) > MAX_UPLOAD_BYTES:
        raise bad_request(size_error_detail)

    return extension


def validate_image_upload(content_type: str | None, contents: bytes, *, size_error_detail: str) -> str:
    """Shared JPEG/PNG/WEBP content-type + 5MB size check used by every
    camera-captured photo-upload endpoint (secure check-in, attendance).
    Returns the file extension to save with. `size_error_detail` lets each
    call site keep its own wording (e.g. "Photo" vs "Image")."""
    return _validate_upload(
        content_type, contents, ALLOWED_IMAGE_CONTENT_TYPES,
        type_error="Only JPEG, PNG or WEBP images are allowed",
        size_error_detail=size_error_detail,
    )


def validate_profile_photo_upload(content_type: str | None, contents: bytes, *, size_error_detail: str) -> str:
    """JPEG/PNG/GIF content-type + 5MB check for trainer/trainee profile
    picture uploads - a deliberately different (and narrower) list from
    validate_image_upload's, which stays WEBP-inclusive for camera
    captures rather than gallery picks."""
    return _validate_upload(
        content_type, contents, ALLOWED_PROFILE_PHOTO_CONTENT_TYPES,
        type_error="Only JPEG, PNG or GIF images are allowed",
        size_error_detail=size_error_detail,
    )


def validate_document_upload(content_type: str | None, contents: bytes, *, size_error_detail: str) -> str:
    """PDF or image (JPEG/PNG/WEBP) + 5MB check for the attendance-sheet upload
    at session check-out. Returns the extension to save with."""
    return _validate_upload(
        content_type, contents, ALLOWED_DOCUMENT_CONTENT_TYPES,
        type_error="Attendance sheet must be a PDF or an image (JPEG/PNG/WEBP)",
        size_error_detail=size_error_detail,
    )


def validate_aadhar_upload(content_type: str | None, contents: bytes, *, size_error_detail: str) -> str:
    """JPEG/PNG/PDF/DOC/DOCX + 5MB check for the trainer's Aadhaar upload."""
    return _validate_upload(
        content_type, contents, ALLOWED_AADHAR_CONTENT_TYPES,
        type_error="Aadhaar file must be a JPEG, PNG, PDF or Word document",
        size_error_detail=size_error_detail,
    )
