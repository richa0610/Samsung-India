import unittest
from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database.common import get_common_db
from app.database.connection import CommonBase, TenantBase
from app.database.tenant import tenant_manager
from app.main import app
from app.models.admin import Admin
from app.models.common.tenant_registry import Tenant
from app.models.trainee import Trainee


class MultiTenancyIntegrationTests(unittest.TestCase):
    def setUp(self):
        # 1. Isolated Common Database
        self.common_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        CommonBase.metadata.create_all(bind=self.common_engine)
        self.CommonSession = sessionmaker(
            autocommit=False, autoflush=False, bind=self.common_engine
        )

        # 2. Isolated Tenant ABC Database
        self.engine_abc = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TenantBase.metadata.create_all(bind=self.engine_abc)
        self.SessionABC = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine_abc
        )

        # 3. Isolated Tenant XYZ Database
        self.engine_xyz = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TenantBase.metadata.create_all(bind=self.engine_xyz)
        self.SessionXYZ = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine_xyz
        )

        # Register isolated engines into tenant manager
        tenant_manager.register_engine("ABC", self.engine_abc)
        tenant_manager.register_engine("XYZ", self.engine_xyz)

        # Seed Common DB Tenants Registry
        common_session = self.CommonSession()
        common_session.add(
            Tenant(
                tenant_uid="ABC",
                company_name="Company ABC",
                database_host="server-a.internal",
                database_port=3306,
                database_name="db_abc",
                database_username="user_abc",
                database_password="secret_password_abc",
                status="active",
            )
        )
        common_session.add(
            Tenant(
                tenant_uid="XYZ",
                company_name="Company XYZ",
                database_host="server-b.internal",
                database_port=3306,
                database_name="db_xyz",
                database_username="user_xyz",
                database_password="secret_password_xyz",
                status="active",
            )
        )
        common_session.commit()
        common_session.close()

        # Seed Trainee in Tenant ABC
        session_abc = self.SessionABC()
        self.trainee_abc = Trainee(
            traineeUid="trainee_abc_1",
            name="Alice ABC",
            phone=9991112222,
            email="alice@abc.com",
            status="Active",
        )
        session_abc.add(self.trainee_abc)
        session_abc.commit()
        session_abc.close()

        # Seed Trainee in Tenant XYZ
        session_xyz = self.SessionXYZ()
        self.trainee_xyz = Trainee(
            traineeUid="trainee_xyz_1",
            name="Bob XYZ",
            phone=9993334444,
            email="bob@xyz.com",
            status="Active",
        )
        session_xyz.add(self.trainee_xyz)
        session_xyz.commit()
        session_xyz.close()

        # Dependency overrides for FastAPI app during tests
        def override_common_db():
            db = self.CommonSession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_common_db] = override_common_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        tenant_manager.close_all()

    def test_tenant_data_isolation(self):
        """Verify user of Tenant ABC reads strictly from ABC's DB,
        and user of Tenant XYZ reads strictly from XYZ's DB."""
        token_abc = create_access_token(subject="9991112222", tenant_id="ABC")
        token_xyz = create_access_token(subject="9993334444", tenant_id="XYZ")

        # Update /me for ABC
        update_resp_abc = self.client.patch(
            "/trainees/me",
            headers={"Authorization": f"Bearer {token_abc}"},
            json={"designation": "Manager ABC"},
        )
        self.assertEqual(update_resp_abc.status_code, 200)
        self.assertEqual(update_resp_abc.json()["trainee"]["name"], "Alice ABC")
        self.assertEqual(update_resp_abc.json()["trainee"]["designation"], "Manager ABC")

        # Update /me for XYZ
        update_resp_xyz = self.client.patch(
            "/trainees/me",
            headers={"Authorization": f"Bearer {token_xyz}"},
            json={"designation": "Director XYZ"},
        )
        self.assertEqual(update_resp_xyz.status_code, 200)
        self.assertEqual(update_resp_xyz.json()["trainee"]["name"], "Bob XYZ")
        self.assertEqual(update_resp_xyz.json()["trainee"]["designation"], "Director XYZ")

        # Verify DB ABC does not have Bob
        session_abc = self.SessionABC()
        self.assertIsNone(session_abc.query(Trainee).filter_by(name="Bob XYZ").first())
        session_abc.close()

        # Verify DB XYZ does not have Alice
        session_xyz = self.SessionXYZ()
        self.assertIsNone(session_xyz.query(Trainee).filter_by(name="Alice ABC").first())
        session_xyz.close()

    def test_zero_trust_client_spoofing_prevented(self):
        """If Alice has a JWT for tenant ABC, passing ?tenant_id=XYZ or
        X-Tenant-ID: XYZ must be IGNORED. Query must still route strictly to ABC."""
        token_abc = create_access_token(subject="9991112222", tenant_id="ABC")

        resp = self.client.patch(
            "/trainees/me?tenant_id=XYZ",
            headers={
                "Authorization": f"Bearer {token_abc}",
                "X-Tenant-ID": "XYZ",
            },
            json={"supervisorName": "Secure Supervisor"},
        )
        self.assertEqual(resp.status_code, 200)
        # Must still be Alice in ABC
        self.assertEqual(resp.json()["trainee"]["name"], "Alice ABC")

        # Verify update went into ABC DB, NOT XYZ DB
        session_xyz = self.SessionXYZ()
        self.assertIsNone(session_xyz.query(Trainee).filter_by(supervisorName="Secure Supervisor").first())
        session_xyz.close()

        session_abc = self.SessionABC()
        alice = session_abc.query(Trainee).filter_by(supervisorName="Secure Supervisor").first()
        self.assertIsNotNone(alice)
        self.assertEqual(alice.name, "Alice ABC")
        session_abc.close()

    def test_failure_isolation_tenant_outage(self):
        """Simulate Tenant ABC database going down:
        ABC requests must get HTTP 503 with generic error.
        XYZ requests must continue working with 200 OK.
        FastAPI process must remain completely alive and operational."""
        token_abc = create_access_token(subject="9991112222", tenant_id="ABC")
        token_xyz = create_access_token(subject="9993334444", tenant_id="XYZ")

        def broken_get_session(tenant_uid, common_db=None):
            if tenant_uid == "ABC":
                mock_session = MagicMock()
                mock_session.query.side_effect = OperationalError(
                    "Can't connect to MySQL server on 'server-a.internal'",
                    params={},
                    orig=Exception("Connection refused"),
                )
                return mock_session
            return self.SessionXYZ()

        with patch.object(tenant_manager, "get_session", side_effect=broken_get_session):
            resp_abc = self.client.patch(
                "/trainees/me",
                headers={"Authorization": f"Bearer {token_abc}"},
                json={"designation": "Outage Test"},
            )
            self.assertEqual(resp_abc.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn("Tenant database is temporarily unavailable", resp_abc.json()["detail"])
            self.assertNotIn("server-a.internal", resp_abc.text)
            self.assertNotIn("secret_password_abc", resp_abc.text)

            resp_xyz = self.client.patch(
                "/trainees/me",
                headers={"Authorization": f"Bearer {token_xyz}"},
                json={"designation": "Still Running Smoothly"},
            )
            self.assertEqual(resp_xyz.status_code, 200)
            self.assertEqual(resp_xyz.json()["trainee"]["name"], "Bob XYZ")

    def test_inactive_tenant_denial(self):
        """A tenant marked inactive or suspended should be denied access."""
        common_session = self.CommonSession()
        common_session.add(
            Tenant(
                tenant_uid="SUSPENDED_CORP",
                company_name="Suspended Corp",
                database_host="localhost",
                database_port=3306,
                database_name="suspended_db",
                database_username="u",
                database_password="p",
                status="inactive",
            )
        )
        common_session.commit()
        common_session.close()

        token_suspended = create_access_token(subject="12345", tenant_id="SUSPENDED_CORP")
        resp = self.client.patch(
            "/trainees/me",
            headers={"Authorization": f"Bearer {token_suspended}"},
            json={"designation": "Test"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("inactive", resp.json()["detail"].lower())

    def test_admin_lookup_uses_common_db_not_tenant_db(self):
        """Regression test for the ripple this port required: Admin moved to
        the Common DB, so /admin/login (superadmin branch) and
        get_current_admin must resolve Admin rows there, not in whichever
        tenant DB happens to be active for the request."""
        common_session = self.CommonSession()
        from app.core.security import hash_password

        common_session.add(
            Admin(
                adminUid="admin-1",
                username="demoadmin",
                password=hash_password("Sup3rSecret!"),
                name="Demo Admin",
                role="admin",
            )
        )
        common_session.commit()
        common_session.close()

        resp = self.client.post(
            "/admin/login",
            headers={"X-Tenant-ID": "ABC"},
            json={"username": "demoadmin", "password": "Sup3rSecret!"},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["admin"]["username"], "demoadmin")
        self.assertEqual(body["admin"]["tenant_id"], "ABC")


if __name__ == "__main__":
    unittest.main()
