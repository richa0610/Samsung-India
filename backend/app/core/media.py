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

# Trainer/trainee profile picture specifically - a deliberately different
# (and narrower) list from ALLOWED_IMAGE_CONTENT_TYPES above, which stays
# JPEG/PNG/WEBP for camera-captured photos (check-in, attendance) since
# that's what the camera hardware actually produces. Profile pictures are
# picked from the user's gallery instead, where a GIF is a real
# possibility worth allowing - WEBP isn't part of this spec.
ALLOWED_PROFILE_PHOTO_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
}

# Attendance-sheet upload at session check-out: a scan/photo of the signed
# sheet, or a PDF. No spreadsheets - just what a printed sheet comes back as.
ALLOWED_DOCUMENT_CONTENT_TYPES = {
    **ALLOWED_IMAGE_CONTENT_TYPES,
    "application/pdf": "pdf",
}

# Aadhaar upload: an image scan, a PDF, or a Word doc of the card.
ALLOWED_AADHAR_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


def media_subdir(name: str) -> Path:
    path = MEDIA_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path
