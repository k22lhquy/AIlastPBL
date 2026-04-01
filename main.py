# from fastapi import FastAPI
# from routes import auth_routes, user_routes, chat_box_routes

# app = FastAPI()

# app.include_router(auth_routes.router, prefix="/auth")
# app.include_router(user_routes.router, prefix="/users")
# app.include_router(chat_box_routes.router, prefix="/chat-box")

# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes, user_routes, chat_box_routes
from configs.firebase_config import initialize_firebase

app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
app.include_router(user_routes.router, prefix="/users", tags=["Users"])
app.include_router(chat_box_routes.router, prefix="/chat-box", tags=["Chat Box"])

@app.on_event("startup")
async def startup_event():
    # Initialize Firebase
    initialize_firebase()
    print("✓ Application started successfully")

@app.get("/")
def root():
    return {
        "message": "Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }