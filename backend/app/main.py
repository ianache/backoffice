from fastapi import FastAPI
from app.domains.tenants.router import router as tenants_router
from app.domains.users.router import router as users_router

app = FastAPI(title="BackOffice Backend", version="1.0.0")

app.include_router(tenants_router)
app.include_router(users_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backoffice-backend"}
