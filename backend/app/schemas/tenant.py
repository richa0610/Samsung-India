from pydantic import BaseModel


class TenantOut(BaseModel):
    """A company the app signs people in to: the ID it sends as X-Tenant-ID, and the name it shows."""

    tenantId: str
    companyName: str
