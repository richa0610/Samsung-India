"""Signs in as each demo account. The password comes from DEMO_SEED_PASSWORD - the one
seed_demo_company_users.py was given or wrote to backups/demo-accounts-<time>.txt."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASSWORD = os.environ.get("DEMO_SEED_PASSWORD", "").strip()
if not PASSWORD:
    sys.exit("Set DEMO_SEED_PASSWORD to the demo accounts' password first.")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Tenant lookup
lookup = client.get('/tenants/lookup?code=demo')
assert lookup.status_code == 200, lookup.text
print('Tenant lookup success:', lookup.json())

# 2. Admin 1 & 2 login
for adm in ['demoadmin1', 'demoadmin2']:
    res = client.post('/admin/login', json={'username': adm, 'password': PASSWORD}, headers={'X-Tenant-ID': 'demo'})
    assert res.status_code == 200, f'Admin {adm} failed: {res.text}'
    role = res.json()["admin"]["role"]
    print(f'Admin {adm} login OK: {role}')

# 3. Trainers login (by phone and by offerId)
for trn in ['9811122001', 'OFF26002', '9811122003']:
    res = client.post('/admin/login', json={'username': trn, 'password': PASSWORD}, headers={'X-Tenant-ID': 'demo'})
    assert res.status_code == 200, f'Trainer {trn} failed: {res.text}'
    name = res.json()["admin"]["name"]
    print(f'Trainer {trn} login OK: {name}')

# 4. Trainees login (by phone and by username)
for identifier in ['9822001101', 'demotrainee2', '9822001103', 'demotrainee4']:
    res = client.post('/trainees/login', json={'identifier': identifier, 'password': PASSWORD}, headers={'X-Tenant-ID': 'demo'})
    assert res.status_code == 200, f'Trainee {identifier} failed: {res.text}'
    name = res.json()["trainee"]["name"]
    print(f'Trainee {identifier} login OK: {name}')

print('\nALL 9 ACCOUNTS VERIFIED AND READY!')
