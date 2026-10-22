"""cPanel's API (UAPI) - the only way a Bluehost account may create a MySQL database (user,
2026-10-22): the account's MySQL logins can't run CREATE DATABASE themselves. Used by the automatic
company setup (services/tenant_setup).

Each call is one HTTPS GET to <CPANEL_URL>/execute/<Module>/<function>, authenticated with an API
token made in cPanel (Manage API Tokens) - sent as a header, never in the address, and never
written into an error or a log line."""

from typing import Optional

import httpx


class CpanelError(RuntimeError):
    """cPanel refused a call, or couldn't be reached - the message is safe to show and store."""


class CpanelClient:
    def __init__(self, url: str, user: str, token: str, *, verify_tls: bool = True, timeout: float = 30,
                 transport: Optional[httpx.BaseTransport] = None):
        self._client = httpx.Client(
            base_url=url.rstrip("/"), headers={"Authorization": f"cpanel {user}:{token}"},
            verify=verify_tls, timeout=timeout, transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CpanelClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def call(self, module: str, function: str, **params) -> dict:
        """One UAPI call; its `data` on success, else CpanelError with cPanel's own reason."""
        try:
            response = self._client.get(f"/execute/{module}/{function}", params=params)
        except httpx.HTTPError as exc:
            raise CpanelError(f"cPanel couldn't be reached ({type(exc).__name__})") from None
        if response.status_code in (401, 403):
            raise CpanelError("cPanel refused the API token (check CPANEL_USER and CPANEL_API_TOKEN)")
        if response.status_code >= 400:
            raise CpanelError(f"cPanel answered HTTP {response.status_code} to {module}::{function}")
        try:
            body = response.json()
        except ValueError:
            raise CpanelError(f"cPanel's answer to {module}::{function} wasn't JSON") from None
        result = body.get("result", body)   # /execute/ answers the result itself; older proxies wrap it
        if result.get("status") != 1:
            reasons = result.get("errors") or ["no reason given"]
            raise CpanelError(f"cPanel {module}::{function}: " + "; ".join(str(r) for r in reasons))
        return result.get("data") or {}

    def create_database(self, name: str) -> bool:
        """Creates the database; False when it already exists (a setup interrupted after this step)."""
        try:
            self.call("Mysql", "create_database", name=name)
        except CpanelError as exc:
            if "already exists" in str(exc).lower():
                return False
            raise
        return True

    def grant_all(self, user: str, database: str) -> None:
        """Gives the MySQL login `user` every privilege on `database` (cPanel's "Add User to Database")."""
        self.call("Mysql", "set_privileges_on_database", user=user, database=database, privileges="ALL PRIVILEGES")
