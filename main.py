from fastapi import FastAPI
from routes import auth_routes, user_routes, chat_box_routes

app = FastAPI()

app.include_router(auth_routes.router, prefix="/auth")
app.include_router(user_routes.router, prefix="/users")
app.include_router(chat_box_routes.router, prefix="/chat-box")