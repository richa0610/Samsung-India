import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies.auth import get_current_trainee
from app.dependencies.database import get_tenant_id_from_request
from app.models.trainee import Trainee
from app.schemas.proctoring import FaceCheckRequest, FaceCheckResult
from app.services.face_detection import count_faces
from app.services.proctoring_settings_service import get_proctoring_settings

router = APIRouter(prefix="/proctoring", tags=["proctoring"])


@router.post("/check-frame", response_model=FaceCheckResult)
async def check_frame(
    payload: FaceCheckRequest,
    request: Request,
    trainee: Trainee = Depends(get_current_trainee),
):
    allowed, max_warnings = get_proctoring_settings(get_tenant_id_from_request(request))
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live proctoring is not enabled for your company",
        )

    try:
        face_count = await count_faces(payload.image)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Face detection is not configured on the server",
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Couldn't reach the face detection service",
        )

    return FaceCheckResult(faceCount=face_count, maxWarnings=max_warnings, allowed=allowed)
