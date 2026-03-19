from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_db, close_db
from app.routes import auth, chatbots, chat, api_keys, documents, analytics, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="AI Chat Builder API",
    description="Multi-Provider AI Chat Builder SaaS Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chatbots.router)
app.include_router(chat.router)
app.include_router(api_keys.router)
app.include_router(documents.router)
app.include_router(analytics.router)
app.include_router(public.router)


@app.get("/")
async def root():
    return {
        "message": "AI Chat Builder API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
