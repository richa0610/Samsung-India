from pathlib import Path

from app.core.config import settings

# Uploaded files are organized into subfolders by kind, e.g.
# media/trainee_photos, served (with auth) at /media - see
# app/routers/media.py. MEDIA_ROOT_PATH points this at a persistent disk in
# production; unset (local dev), it falls back to backend/media in the repo.
MEDIA_ROOT = (
    Path(settings.MEDIA_ROOT_PATH)
    if settings.MEDIA_ROOT_PATH
    else Path(__file__).resolve().parent.parent.parent / "media"
)

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


def default_trainer_avatar(gender: str | None) -> str:
    """Gender-based fallback path shown until a trainer uploads a real
    profile photo. Served from the same /media route as a real upload (see
    routers/media.py), so the frontend needs no special-casing between a
    real photo and this default - it's just another path to resolve and
    fetch. `gender` is a free-text field on both Admin and AgencyTeam (no
    fixed set of values), so this only branches on it actually saying
    "male"; everything else (typed as "Female", blank, or anything else)
    gets the female default."""
    if (gender or "").strip().lower() == "male":
        return "trainer_photos/default_male.png"
    return "trainer_photos/default_female.png"


# The legacy PHP system's `agencyteam.profilePhoto` column defaults to this
# literal string at the DB level (see the schema dump) rather than NULL/"" -
# an account that's never uploaded a photo carries this exact value, not an
# empty one, so `photo or default_trainer_avatar(...)` alone would miss it
# and try to serve a file that was never actually uploaded.
_LEGACY_NO_PHOTO_SENTINEL = "defaultfile.png"


def resolve_trainer_avatar(photo_path: str | None, gender: str | None) -> str:
    """The one place to turn a trainer's raw `profilePhoto` column value
    into what the API should actually return - a real uploaded path as-is,
    or the gender-based default for every "nothing real here" case
    (NULL/empty, or the legacy sentinel above)."""
    if photo_path and photo_path != _LEGACY_NO_PHOTO_SENTINEL:
        return photo_path
    return default_trainer_avatar(gender)
