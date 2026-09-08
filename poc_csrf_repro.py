from fastapi.testclient import TestClient
from src.api.routes import app

c = TestClient(app)
r = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
print("login:", r.status_code)
token = r.json().get("session_token", "")
print("cookie soc_session present:", "soc_session" in c.cookies)

# POST with Bearer token only (what the failing tests do)
r2 = c.post("/api/auth/2fa/setup", headers={"Authorization": f"Bearer {token}"})
print("2fa/setup Bearer:", r2.status_code, r2.json())

# Same POST but with session cookie removed
c.cookies.clear()
r3 = c.post("/api/auth/2fa/setup", headers={"Authorization": f"Bearer {token}"})
print("2fa/setup no-cookie:", r3.status_code, str(r3.json())[:120])
