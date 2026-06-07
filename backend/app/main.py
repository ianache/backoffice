from fastapi import FastAPI
from app.domains.tenants.router import router as tenants_router

app = FastAPI(title="BackOffice Backend", version="1.0.0")

app.include_router(tenants_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backoffice-backend"}
