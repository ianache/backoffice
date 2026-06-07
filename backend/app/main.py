from fastapi import FastAPI

app = FastAPI(title="BackOffice Backend", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backoffice-backend"}
