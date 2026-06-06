from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import SessionLocal
from app.services.seed_service import init_db, seed_if_empty
from app.api import auth, products, knowledge, quotes, chat, admin, tools

app = FastAPI(title="The Blue Red - AI Powered Proposal Assistant Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize immediately too, so TestClient/import-based tests and CLI demos work without lifespan context.
init_db()
_db = SessionLocal()
try:
    seed_if_empty(_db)
finally:
    _db.close()

@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/seed")
def seed():
    db = SessionLocal()
    try:
        return seed_if_empty(db)
    finally:
        db.close()

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(knowledge.router)
app.include_router(quotes.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(tools.router)
