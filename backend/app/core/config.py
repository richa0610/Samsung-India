from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Path to a CA certificate file, required by managed MySQL providers that
    # enforce TLS (e.g. Aiven - download it from the service's "Connection
    # Information" panel). Leave blank for a plain local MySQL with no TLS.
    DB_SSL_CA: str = ""

    # Common Database settings (shared registry: admin, system_modules,
    # tenants). Falls back to DB_* if not explicitly defined, so a
    # single-tenant deployment needs no extra configuration.
    COMMON_DB_HOST: Optional[str] = None
    COMMON_DB_PORT: Optional[int] = None
    COMMON_DB_USER: Optional[str] = None
    COMMON_DB_PASSWORD: Optional[str] = None
    COMMON_DB_NAME: Optional[str] = None

    # Multi-tenancy settings
    DEFAULT_TENANT_ID: str = "samsung"
    TENANT_POOL_SIZE: int = 5
    TENANT_MAX_OVERFLOW: int = 10
    TENANT_POOL_TIMEOUT: int = 10
    TENANT_POOL_RECYCLE: int = 280

    # Set by the test suite (see tests/__init__.py). It switches OFF everything the
    # app normally does to the database on import / startup (create_all, column and
    # index sync, keep-alive pings), and Settings refuses to load at all if it is
    # set while pointing at a non-local database - so a test can never initialise
    # or alter a real database, whatever .env contains.
    TESTING: bool = False

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    # bcrypt cost for NEW password hashes (core/security.py) - an existing hash keeps the cost it
    # was made with. 10 = the cost used before this was configurable, so an environment that
    # doesn't set it behaves exactly as before. Bounded so a typo can neither weaken hashing below
    # that nor make every hash so slow it ties up the server (each +1 doubles the time; 12 already
    # takes ~2 s on the production CPU).
    BCRYPT_ROUNDS: int = Field(default=10, ge=10, le=14)

    # Network settings used by the local Uvicorn development server. Binding
    # to all interfaces lets phones on the same Wi-Fi reach this machine.
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    ALLOW_ATTENDANCE_RETEST: bool = False
    # QR codes shared before join codes were signed (the bare training ID) are accepted until this
    # IST date (inclusive), then refused. Empty = signed codes only. See app/utils/join_code.py.
    JOIN_CODE_LEGACY_UNTIL: str = "2026-10-31"

    # How many reverse proxies sit in front of this API and append the caller's address to
    # X-Forwarded-For. Production is behind Render's proxy only (1): the LAST entry is the one
    # Render added, so it's the real caller - everything before it is whatever the client sent
    # and is never trusted. 0 = no proxy (use the socket peer, e.g. local LAN testing).
    TRUSTED_PROXY_HOPS: int = 1
    # Per-tenant cap on requests in progress (app/core/tenant_limit.py): below the 40 worker threads
    # the app's regular endpoints share, so one tenant with a hung database can't take them all.
    # Requests over the cap wait (without a thread) up to TENANT_QUEUE_WAIT_SECONDS, then get a 503.
    TENANT_MAX_CONCURRENT_REQUESTS: int = 25
    TENANT_QUEUE_WAIT_SECONDS: float = 15

    # Comma-separated Fernet keys that encrypt tenant database passwords at rest (core/secret_box.py).
    # The first key encrypts, any listed key decrypts. Empty = not configured yet: existing
    # plaintext rows keep working and new ones stay plaintext until a key is set.
    TENANT_SECRETS_KEYS: str = ""

    # Absolute path to a persistent disk mount for uploaded files (profile
    # photos, Aadhaar docs, attendance photos/sheets, etc). Left blank, media
    # falls back to a folder inside the repo checkout - fine for local dev,
    # but on a host with an ephemeral filesystem (e.g. Render's free plan)
    # that folder is wiped on every deploy, silently 404ing every file
    # uploaded before the last deploy. Set this to a mounted disk's path in
    # production so uploads survive deploys/restarts.
    MEDIA_ROOT_PATH: str = ""

    # Swagger/OpenAPI (`/docs`, `/openapi.json`) expose the full route map -
    # fine for local/LAN dev, worth turning off (set to "false" in .env)
    # before this ever sits behind a public URL.
    DEBUG: bool = True

    # Fallback warning count for tenants whose registry row has no explicit
    # proctoring_max_warnings value.
    DEFAULT_PROCTORING_MAX_WARNINGS: int = 3

    # Comma-separated list of origins allowed to call this API from a
    # browser (CORS). Only relevant for `expo start --web` / browser
    # clients - native Expo Go / dev-client requests don't send an Origin
    # header, so this never affects phone testing. Add your machine's LAN
    # IP (e.g. "http://192.168.1.23:8081") if you test the web build from
    # another device. Set to "*" only for throwaway local debugging.
    ALLOWED_ORIGINS: str = "http://localhost:8081,http://localhost:19006,http://localhost:8082"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @model_validator(mode="after")
    def _refuse_remote_database_when_testing(self):
        if self.TESTING:
            for host in (self.DB_HOST, self.common_db_host):
                if host not in ("127.0.0.1", "localhost", "::1"):
                    raise ValueError(
                        "TESTING is set but the database host is not local - refusing to start "
                        "so tests can never touch a real database."
                    )
        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def common_db_host(self) -> str:
        return self.COMMON_DB_HOST or self.DB_HOST

    @property
    def common_db_port(self) -> int:
        return self.COMMON_DB_PORT or self.DB_PORT

    @property
    def common_db_user(self) -> str:
        return self.COMMON_DB_USER or self.DB_USER

    @property
    def common_db_password(self) -> str:
        return self.COMMON_DB_PASSWORD or self.DB_PASSWORD

    @property
    def common_db_name(self) -> str:
        return self.COMMON_DB_NAME or self.DB_NAME


settings = Settings()
