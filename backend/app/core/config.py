from typing import Optional

from pydantic_settings import BaseSettings


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

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Network settings used by the local Uvicorn development server. Binding
    # to all interfaces lets phones on the same Wi-Fi reach this machine.
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    ALLOW_ATTENDANCE_RETEST: bool = False

    # Swagger/OpenAPI (`/docs`, `/openapi.json`) expose the full route map -
    # fine for local/LAN dev, worth turning off (set to "false" in .env)
    # before this ever sits behind a public URL.
    DEBUG: bool = True

    # Google Cloud Vision API key used for proctoring face-count checks
    # during assessments. Leave blank to disable server-side face checks.
    FACE_DETECTION_API_KEY: str = ""

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
