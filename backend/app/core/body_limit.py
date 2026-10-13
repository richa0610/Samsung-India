"""Refuses a request whose body is bigger than the app ever needs, before the server stores it.

Each uploaded file is capped at 5MB (utils/validators.py), but the multipart parser writes the
WHOLE incoming body to a temporary file before any endpoint runs - so without this, one huge
upload would still be received and stored in full. A body over `max_bytes` gets 413: at once when
its declared Content-Length says so, otherwise as soon as the bytes actually received pass it.
"""

from fastapi import HTTPException
from starlette.responses import JSONResponse

TOO_LARGE = "Upload is too large. Each file must be 5MB or smaller."


class BodySizeLimit:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > self.max_bytes:
            await JSONResponse({"detail": TOO_LARGE}, status_code=413)(scope, receive, send)
            return

        received = 0

        async def counted_receive():
            # A body sent without a Content-Length (chunked) is counted as it arrives. The 413 is
            # raised from inside the endpoint's body parsing, so FastAPI answers it as usual.
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise HTTPException(status_code=413, detail=TOO_LARGE)
            return message

        await self.app(scope, counted_receive, send)
