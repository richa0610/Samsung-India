from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import AuthenticatedAccount, get_current_account
from app.dependencies.database import get_common_db
from app.schemas.tenant import TenantOut
from app.services import tenant_directory

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/lookup", response_model=TenantOut)
def lookup_company(code: str = Query(..., min_length=1, max_length=100), common_db: Session = Depends(get_common_db)):
    """The company a typed company code names, so the app can confirm it before anyone signs in.
    Public: it runs before sign-in. Answers only an active company's ID and name - the same 404 for
    an unknown code and for a suspended company."""
    return tenant_directory.lookup(common_db, code)


@router.get("/current", response_model=TenantOut)
def current_company(account: AuthenticatedAccount = Depends(get_current_account), common_db: Session = Depends(get_common_db)):
    """The company the caller's token was issued for - lets an app signed in before company codes
    existed learn which company it is in."""
    return tenant_directory.describe(common_db, account.tenant_id)
