from fastapi import FastAPI
from app.domains.tenants.router import router as tenants_router
from app.domains.users.router import router as users_router
from app.domains.feature_flags.router import router as flags_router
from app.domains.feature_flags.router import segments_router
from app.domains.products.router import router as products_router
from app.domains.companies.router import router as companies_router
from app.domains.audit.router import router as audit_router
from app.ws.connection_manager import ConnectionManager
from app.domains.sdk.router import router as sdk_router
from app.domains.sdk.ws_router import ws_flags_endpoint

app = FastAPI(title="BackOffice Backend", version="1.0.0")

# ConnectionManager MUST be initialized before any router that accesses app.state.ws_manager
app.state.ws_manager = ConnectionManager()

app.include_router(tenants_router)
app.include_router(users_router)
app.include_router(flags_router)
app.include_router(segments_router)
app.include_router(products_router)
app.include_router(companies_router)
app.include_router(audit_router)
app.include_router(sdk_router)          # /api/v1/sdk/bootstrap, /evaluate, /eval-events
app.add_websocket_route("/ws/flags/{tenant_id}", ws_flags_endpoint)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backoffice-backend"}
