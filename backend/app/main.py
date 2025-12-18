from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

# Importa il nostro NUOVO agente Gemini
try:
    from .gemini_agent import GeminiOrientationAgent, orientation_agent
    from .state_manager import state_manager
    from .student_profile import StudentProfile
    AGENT_AVAILABLE = orientation_agent is not None
except ImportError as e:
    print(f"⚠️  Errore import agente avanzato: {e}")
    # Fallback all'agente semplice
    try:
        from .agent.simple_agent import SimpleCareerAgent
        orientation_agent = SimpleCareerAgent()
        AGENT_AVAILABLE = True
        print("✅ Usando agente semplice di fallback")
    except ImportError:
        orientation_agent = None
        AGENT_AVAILABLE = False
        print("❌ Nessun agente disponibile")

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelli Pydantic (MANTENIAMO GLI STESSI per compatibilità)
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

# Crea l'app FastAPI
app = FastAPI(
    title="Career Guidance Agent API",
    description="API per l'agente AI avanzato di orientamento universitario",
    version="2.0.0",
)

# Configura CORS (stesse origini per compatibilità)
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
        "message": "Career Guidance Agent API v2.0",
        "status": "running",
        "agent_available": AGENT_AVAILABLE,
        "agent_type": "GeminiOrientationAgent" if AGENT_AVAILABLE and hasattr(orientation_agent, 'process_message') else "SimpleCareerAgent",
        "version": "2.0.0",
        "endpoints": ["/health", "/api/chat", "/api/recommendations", "/docs", "/api/profile/{session_id}"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if AGENT_AVAILABLE else "degraded",
        "agent_ready": AGENT_AVAILABLE,
        "agent_type": "advanced" if hasattr(orientation_agent, 'process_message') else "simple",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Endpoint per la chat con l'agente AI avanzato"""
    try:
        if not AGENT_AVAILABLE:
            raise HTTPException(status_code=503, detail="Agente non disponibile")
        
        # Gestione sessione con il nostro state_manager
        session_id = request.session_id
        
        if not session_id:
            # Crea nuova sessione
            if hasattr(orientation_agent, 'start_new_conversation'):
                # Nuovo agente Gemini
                welcome_message, profile = orientation_agent.start_new_conversation()
                session_id = profile.session_id
                initial_history = [{
                    "user": "(session_start)",
                    "agent": welcome_message,
                    "timestamp": datetime.now().isoformat()
                }]
            else:
                # Agente semplice di fallback
                session_id = str(uuid.uuid4())
                initial_history = []
            
            # Inizializza sessione nello state_manager
            if hasattr(state_manager, 'create_session'):
                state_manager.create_session()
        
        # Processa il messaggio
        if hasattr(orientation_agent, 'process_message'):
            # Nuovo agente Gemini
            response, profile = orientation_agent.process_message(session_id, request.message)
            
            # Prepara raccomandazioni se il profilo è completo
            recommendations = []
            if profile and profile.is_sufficient_for_search():
                recommendations = [
                    {
                        "type": "university",
                        "name": f"Corsi in {', '.join(profile.favorite_subjects[:2]) if profile.favorite_subjects else 'tua zona'}",
                        "match_score": 0.9,
                        "reason": f"Basato sui tuoi interessi in {', '.join(profile.favorite_subjects[:2]) if profile.favorite_subjects else 'materie scientifiche'}"
                    }
                ]
            
            # Prepara cronologia conversazione
            conversation_history = []
            if profile and hasattr(profile, 'conversation_history'):
                for turn in profile.conversation_history[-10:]:  # Ultimi 10 messaggi
                    conversation_history.append({
                        "user": turn["message"] if turn["role"] == "user" else "",
                        "agent": turn["message"] if turn["role"] == "agent" else "",
                        "timestamp": turn.get("timestamp", datetime.now().isoformat())
                    })
            else:
                conversation_history = [{
                    "user": request.message,
                    "agent": response,
                    "timestamp": datetime.now().isoformat()
                }]
        else:
            # Fallback all'agente semplice
            response = orientation_agent.process_message(request.message)
            recommendations = []
            conversation_history = [{
                "user": request.message,
                "agent": response,
                "timestamp": datetime.now().isoformat()
            }]
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            recommendations=recommendations,
            conversation_history=conversation_history[-5:]  # Ultimi 5 messaggi
        )
        
    except Exception as e:
        logger.error(f"Errore in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Endpoint per raccomandazioni basate su profilo"""
    try:
        # Usa il web searcher se disponibile
        recommendations = []
        
        if hasattr(orientation_agent, 'web_searcher'):
            try:
                from .web_searcher import WebSearcher
                searcher = WebSearcher()
                
                profile_data = {
                    "favorite_subjects": request.interests,
                    "location": request.location,
                    "school_type": ""
                }
                
                search_results = searcher.search_for_student_profile(profile_data)
                
                for rec in search_results.get("recommendations", [])[:3]:
                    recommendations.append({
                        "type": "university" if "🎓" in rec else "its" if "🔧" in rec else "general",
                        "name": rec.replace("🎓", "").replace("🔧", "").replace("📊", "").strip(),
                        "match_score": 0.85,
                        "reason": "Basato su ricerca web aggiornata"
                    })
            except Exception as search_error:
                logger.warning(f"Errore ricerca web: {search_error}")
                # Fallback a raccomandazioni di base
        
        # Se non abbiamo raccomandazioni dalla ricerca web, usa quelle di base
        if not recommendations:
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

@app.get("/api/profile/{session_id}")
async def get_profile_info(session_id: str):
    """Endpoint per ottenere informazioni sul profilo dello studente"""
    try:
        if not AGENT_AVAILABLE or not hasattr(state_manager, 'get_session'):
            raise HTTPException(status_code=501, detail="Funzionalità non disponibile")
        
        profile = state_manager.get_session(session_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Sessione non trovata")
        
        return {
            "session_id": session_id,
            "location": profile.location,
            "school_type": profile.school_type,
            "favorite_subjects": profile.favorite_subjects,
            "primary_goal": profile.primary_goal,
            "completeness": profile.profile_completeness,
            "ready_for_search": profile.is_sufficient_for_search(),
            "missing_info": profile.missing_info_priority[:3]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore in profile endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test")
async def test_endpoint():
    """Endpoint di test"""
    return {
        "message": "API v2.0 funzionante con agente avanzato!" if AGENT_AVAILABLE else "API in modalità fallback",
        "agent_available": AGENT_AVAILABLE,
        "agent_type": "advanced" if hasattr(orientation_agent, 'process_message') else "simple",
        "timestamp": datetime.now().isoformat(),
        "endpoints_available": ["/", "/health", "/api/chat", "/api/recommendations", "/api/profile/{id}", "/docs"]
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
