"""Production-ish entrypoint: same app as run.py but without --reload and
with access logging, for serving real users through the Cloudflare tunnel.

    venv/Scripts/python.exe run_prod.py

Keep workers at 1: the login rate-limiter (app/core/rate_limit.py) and the
live-events WebSocket registry (app/routers/ws.py) both hold state in a
single process. Scaling past one worker needs those moved to Redis first.
"""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=False,
        workers=1,
        access_log=True,
    )
