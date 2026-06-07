from fastapi import FastAPI
from app.domains.tenants.router import router as tenants_router
from app.domains.users.router import router as users_router
from app.domains.feature_flags.router import router as flags_router
from app.domains.feature_flags.router import segments_router

app = FastAPI(title="BackOffice Backend", version="1.0.0")

app.include_router(tenants_router)
app.include_router(users_router)
app.include_router(flags_router)
app.include_router(segments_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backoffice-backend"}
