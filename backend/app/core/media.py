import re
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

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB per file
# Whole request body: the largest upload carries two files (check-out photo + attendance sheet)
# plus a few form fields. Anything bigger is refused before it's read (see core/body_limit.py).
MAX_REQUEST_BYTES = 2 * MAX_UPLOAD_BYTES + 1024 * 1024

JPEG = "image/jpeg"
PDF = "application/pdf"

# Only JPEG and PDF are accepted (user, 2026-10-08): photos - profile pictures, check-in and
# training start/end photos - are JPEG; documents - the Aadhaar card, the signed attendance
# sheet - are JPEG or PDF. Files stored before this rule (PNG, WEBP, Word...) are still served.
ALLOWED_PHOTO_CONTENT_TYPES = {JPEG: "jpg"}
ALLOWED_DOCUMENT_CONTENT_TYPES = {JPEG: "jpg", PDF: "pdf"}

# The bytes each accepted type's content really starts with, so a file is checked by what it is,
# not only by the type the client declares for it.
FILE_SIGNATURES = {JPEG: b"\xff\xd8\xff", PDF: b"%PDF-"}


# A tenant's files live in their own folder, MEDIA_ROOT/<tenant_uid>/<kind>/..., so two tenants'
# identically named uploads (agency_3.pdf, the same trainee UID, ...) can never overwrite or
# reveal each other. The path stored in the database stays relative to that folder
# ("trainee_photos/X.jpg"), so API responses and URLs are unchanged; /media resolves it inside the
# caller's own tenant folder (routers/media.py).
_TENANT_FOLDER = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]{0,99}$")


def tenant_folder(tenant_id: str | None) -> str:
    """The folder name for a verified tenant id - refused (ValueError) unless it is a plain name,
    so a tenant id can never point outside MEDIA_ROOT."""
    folder = (tenant_id or "").strip()
    if not _TENANT_FOLDER.match(folder):
        raise ValueError("Unusable tenant id for media storage")
    return folder


def media_subdir(name: str, tenant_id: str | None) -> Path:
    path = MEDIA_ROOT / tenant_folder(tenant_id) / name
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
