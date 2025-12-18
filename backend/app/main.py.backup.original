from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging

# Importa il nostro agente
from .agent.simple_agent import SimpleCareerAgent

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelli Pydantic
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    recommendations: Optional[List] = None
    conversation_history: List[dict]

class RecommendationRequest(BaseModel):
    interests: List[str]
    skills: List[str]
    location: Optional[str] = None
    budget: Optional[float] = None

# Stato applicazione
class AppState:
    def __init__(self):
        self.agent = SimpleCareerAgent()
        self.sessions = {}  # session_id -> conversazione

app_state = AppState()

# Crea l'app FastAPI
app = FastAPI(
    title="Career Guidance Agent API",
    description="API per l'agente AI di orientamento post-diploma",
    version="1.0.0",
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://fluffy-waddle-5g99rp4w79346xq-3000.app.github.dev",
        "https://fluffy-waddle-5g99rp4w79346xq-8000.app.github.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint root"""
    return {
        "message": "Career Guidance Agent API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": ["/health", "/api/chat", "/api/recommendations", "/docs"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_ready": True,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Endpoint per la chat con l'agente AI"""
    try:
        # Gestisci sessione
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in app_state.sessions:
            app_state.sessions[session_id] = {
                "history": [],
                "created_at": datetime.now().isoformat()
            }
        
        # Processa messaggio con l'agente
        agent_response = app_state.agent.process_message(request.message)
        
        # Aggiorna storia conversazione
        conversation_entry = {
            "user": request.message,
            "agent": agent_response,
            "timestamp": datetime.now().isoformat()
        }
        
        app_state.sessions[session_id]["history"].append(conversation_entry)
        
        # Mantieni solo ultime 20 messaggi per sessione
        if len(app_state.sessions[session_id]["history"]) > 20:
            app_state.sessions[session_id]["history"] = app_state.sessions[session_id]["history"][-20:]
        
        return ChatResponse(
            response=agent_response,
            session_id=session_id,
            recommendations=[],  # Per ora vuoto
            conversation_history=app_state.sessions[session_id]["history"][-5:]  # Ultimi 5 messaggi
        )
        
    except Exception as e:
        logger.error(f"Errore in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Endpoint per raccomandazioni basate su profilo"""
    try:
        # Per ora risposta semplice
        recommendations = [
            {
                "type": "university",
                "name": "Informatica",
                "match_score": 0.85,
                "reason": "Basato sui tuoi interessi in tecnologia"
            },
            {
                "type": "its",
                "name": "ITS per lo Sviluppo Software",
                "match_score": 0.78,
                "reason": "Ottimo per entrare rapidamente nel mondo del lavoro"
            }
        ]
        
        return {
            "recommendations": recommendations,
            "profile_analysis": {
                "interests": request.interests,
                "skills": request.skills,
                "location": request.location,
                "budget": request.budget
            }
        }
        
    except Exception as e:
        logger.error(f"Errore in recommendations endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test")
async def test_endpoint():
    """Endpoint di test"""
    return {
        "message": "API funzionante!",
        "timestamp": datetime.now().isoformat(),
        "endpoints_available": ["/", "/health", "/api/chat", "/api/recommendations", "/docs"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
