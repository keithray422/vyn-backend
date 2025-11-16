from fastapi import FastAPI
from app.api.v1 import routes
from app.api.v1 import chat_routes
from app.api.v1 import message_routes
from app.api.v1 import chat_ws
from app.api.v1 import ws as ws_module

def create_app() -> FastAPI:
    app = FastAPI(title="Vyn Backend")

    # Include each router ONCE
    app.include_router(ws_module.router, prefix="/api/v1")
    app.include_router(routes.router, prefix="/api/v1")
    app.include_router(message_routes.router, prefix="/api/v1")
    app.include_router(chat_routes.router, prefix="/api/v1")
    app.include_router(chat_ws.router, prefix="/api/v1")

    return app

app = create_app()
