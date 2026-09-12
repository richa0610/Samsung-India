from pathlib import Path

# backend/media - served statically at /media (see main.py). Uploaded
# files are organized into subfolders by kind, e.g. media/trainee_photos.
MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent / "media"

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

# Attendance-sheet upload at session check-out: a scan/photo of the signed
# sheet, or a PDF. No spreadsheets - just what a printed sheet comes back as.
ALLOWED_DOCUMENT_CONTENT_TYPES = {
    **ALLOWED_IMAGE_CONTENT_TYPES,
    "application/pdf": "pdf",
}


def media_subdir(name: str) -> Path:
    path = MEDIA_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path
