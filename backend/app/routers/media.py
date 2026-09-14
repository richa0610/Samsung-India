from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.media import MEDIA_ROOT
from app.dependencies.auth import get_current_principal

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{file_path:path}")
def get_media_file(
    file_path: str,
    _principal: str = Depends(get_current_principal),
) -> FileResponse:
    """Serves uploaded check-in/checkout photos and attendance sheets.

    Was a blanket `StaticFiles` mount with no auth at all - any trainee /
    trainer / admin token is enough to view a file (there's no per-training
    ownership check), but an anonymous request is rejected. `resolve()` +
    the `MEDIA_ROOT` prefix check block `../` path traversal outside the
    media directory.
    """
    resolved = (MEDIA_ROOT / file_path).resolve()
    if MEDIA_ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(resolved)
