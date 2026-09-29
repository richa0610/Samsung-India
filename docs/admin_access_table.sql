-- admin_access: who may access which tenant / company / zone / region (Phase C, step 1).
--
-- FOR REVIEW. Nothing in the app creates this table: the model is registered on its own
-- metadata (app/models/admin_access.py), so the backend's startup create_all cannot make it.
-- Run this against the SHARED (common) database only after approval. It is additive: it
-- creates one new table and touches no existing table. CHECK constraints need MySQL 8.0.16+.
--
-- One Company Admin per company: `company_admin_key` ("<tenant>|<company>", trimmed, lower-case)
-- is set only on an ACTIVE company_admin grant and is UNIQUE, so the database itself refuses a
-- second Company Admin for the same company in a tenant. NULLs never collide, so every other
-- role and every deactivated grant is unaffected.
-- Kept in sync with the model by tests/test_access_model.py.
--
CREATE TABLE admin_access (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	admin_id INTEGER NOT NULL, 
	`role` VARCHAR(30) NOT NULL, 
	tenant_uid VARCHAR(100), 
	company VARCHAR(150), 
	zone VARCHAR(100), 
	region VARCHAR(100), 
	active INTEGER NOT NULL DEFAULT 1, 
	granted_by VARCHAR(100), 
	note VARCHAR(255), 
	company_admin_key VARCHAR(300), 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT ck_admin_access_role CHECK (role IN ('super_admin','company_admin','coordinator','sub_coordinator','trainer')), 
	CONSTRAINT ck_admin_access_tenant CHECK ((role = 'super_admin' AND tenant_uid IS NULL) OR (role <> 'super_admin' AND tenant_uid IS NOT NULL)), 
	CONSTRAINT ck_admin_access_company CHECK (role NOT IN ('company_admin','coordinator','sub_coordinator') OR company IS NOT NULL), 
	CONSTRAINT ck_admin_access_zone CHECK (role <> 'coordinator' OR zone IS NOT NULL), 
	CONSTRAINT ck_admin_access_region CHECK (role <> 'sub_coordinator' OR region IS NOT NULL), 
	CONSTRAINT ck_admin_access_company_key CHECK ((role = 'company_admin' AND active = 1) = (company_admin_key IS NOT NULL)), 
	CONSTRAINT uq_admin_access_one_company_admin UNIQUE (company_admin_key)
);

CREATE INDEX ix_admin_access_admin_id ON admin_access (admin_id);
