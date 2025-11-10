from app.api.v1 import ws as ws_module
from fastapi import FastAPI
from app.api.v1 import routes
from app.api.v1 import routes, chat_routes
from app.api.v1 import chat_routes

def create_app() -> FastAPI:
    app = FastAPI(title="Vyn Backend (Dev)")
    app.include_router(ws_module.router, prefix="/api/v1")
    app.include_router(routes.router, prefix="/api/v1")
    app.include_router(chat_routes.router, prefix="/api/v1")
    return app

app = create_app()
from app.api.v1 import message_routes

app.include_router(message_routes.router, prefix="/api/v1")
app.include_router(chat_routes.router, prefix="/api/v1", tags=["Chat"])