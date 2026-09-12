from pydantic import BaseModel, Field

# base64 of a 5 MB image is ~6.8 MB; cap a little above that so an oversized
# or junk payload is rejected before it reaches the face-detection provider
# (which is billed per call and would otherwise process arbitrary bytes).
_MAX_BASE64_IMAGE_CHARS = 8_000_000


class FaceCheckRequest(BaseModel):
    image: str = Field(min_length=1, max_length=_MAX_BASE64_IMAGE_CHARS)  # base64 JPEG, no data URI prefix


class FaceCheckResult(BaseModel):
    faceCount: int
    maxWarnings: int
    allowed: bool = True
