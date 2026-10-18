from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import (
    actions,
    audit,
    auth,
    chat,
    customers,
    tickets,
    users,
    document,
    health,
    knowledge,
    imports,
)
app = FastAPI(
    title="AI Support & Operations Agent",
    version="0.1.0",
    description="Backend API for the AI Support & Operations Agent.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def validate_browser_origin(request, call_next):
    """Reject cross-origin browser writes that bypass CORS via HTML forms."""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/v1/"):
        origin = request.headers.get("origin")
        if origin and origin not in settings.cors_origin_list:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=403, content={"detail": "Request origin is not allowed."})
    return await call_next(request)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(tickets.router)
app.include_router(document.router)
app.include_router(knowledge.router)
app.include_router(actions.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(imports.router)
app.include_router(chat.router)
