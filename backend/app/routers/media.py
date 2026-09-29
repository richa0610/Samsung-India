from pathlib import Path, PurePosixPath
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.media import MEDIA_ROOT, tenant_folder
from app.dependencies.auth import AuthenticatedAccount, get_current_account
from app.dependencies.database import get_common_db, get_db
from app.services import media_access

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{file_path:path}")
def get_media_file(
    file_path: str,
    account: AuthenticatedAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
) -> FileResponse:
    """Serves an uploaded file only to an account allowed to see the record that owns it (see
    services/media_access.py), from the caller's own tenant folder. Every refusal - not
    authorized, another tenant's file, a malformed path, a missing file - is the same 404, so a
    caller can't probe which files exist."""
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if ".." in PurePosixPath(file_path).parts or not media_access.can_read(
        db, common_db, account.principal, account.tenant_id, file_path
    ):
        raise not_found
    resolved = _locate(file_path, account.tenant_id)
    if resolved is None:
        raise not_found
    return FileResponse(resolved)


def _locate(file_path: str, tenant_id: str) -> Optional[Path]:
    """The file in the tenant's own folder. Uploads made before files were split per tenant sit
    directly under MEDIA_ROOT; those are only served to the default tenant (the only one that
    existed then), plus the shared default avatars to everyone."""
    try:
        bases = [MEDIA_ROOT / tenant_folder(tenant_id)]
    except ValueError:
        return None
    if tenant_id == settings.DEFAULT_TENANT_ID or file_path in media_access.SHARED_FILES:
        bases.append(MEDIA_ROOT)
    for base in bases:
        resolved = (base / file_path).resolve()
        # resolve() + the prefix check keep a path from escaping its folder (../, symlinks).
        if base.resolve() in resolved.parents and resolved.is_file():
            return resolved
    return None
