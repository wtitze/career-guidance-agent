"""
Gestore dello stato delle sessioni degli studenti.
Mantiene i profili attivi in memoria o in cache.
"""
from typing import Dict, Optional
import json
from datetime import datetime, timedelta
import os

try:
    from student_profile import StudentProfile
except ImportError:
    from .student_profile import StudentProfile


class StateManager:
    """Gestisce lo stato delle sessioni degli studenti."""
    
    def __init__(self, use_redis: bool = False):
        self.use_redis = use_redis
        self.sessions: Dict[str, StudentProfile] = {}
        
        if use_redis:
            # Redis è opzionale, solo se installato
            try:
                import redis
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", 6379))
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                print("✅ Redis abilitato per la gestione delle sessioni")
            except ImportError:
                print("⚠️  Redis non installato, uso memoria in-RAM")
                self.use_redis = False
                self.redis_client = None
        else:
            self.redis_client = None
    
    def create_session(self) -> StudentProfile:
        """Crea una nuova sessione con profilo studente vuoto."""
        profile = StudentProfile()
        self._store_session(profile.session_id, profile)
        return profile
    
    def get_session(self, session_id: str) -> Optional[StudentProfile]:
        """Recupera una sessione per ID."""
        if self.use_redis and self.redis_client:
            try:
                profile_data = self.redis_client.get(f"session:{session_id}")
                if profile_data:
                    return StudentProfile(**json.loads(profile_data))
            except Exception:
                # Fallback a memoria se Redis fallisce
                pass
        
        # Fallback a memoria
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, profile: StudentProfile) -> bool:
        """Aggiorna una sessione esistente."""
        try:
            self._store_session(session_id, profile)
            return True
        except Exception:
            return False
    
    def _store_session(self, session_id: str, profile: StudentProfile) -> None:
        """Archivia il profilo nella memoria appropriata."""
        if self.use_redis and self.redis_client:
            try:
                profile_data = json.dumps(profile.model_dump())
                self.redis_client.setex(
                    f"session:{session_id}", 
                    timedelta(hours=1), 
                    profile_data
                )
                return
            except Exception:
                # Fallback a memoria
                pass
        
        # Salva in memoria (default)
        self.sessions[session_id] = profile
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> None:
        """Pulizia delle sessioni vecchie (solo per memoria in-RAM)."""
        if not self.use_redis:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, profile in self.sessions.items():
                session_age = current_time - profile.created_at
                if session_age > timedelta(hours=max_age_hours):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
    
    def session_exists(self, session_id: str) -> bool:
        """Verifica se una sessione esiste."""
        if self.use_redis and self.redis_client:
            try:
                return self.redis_client.exists(f"session:{session_id}") == 1
            except Exception:
                return session_id in self.sessions
        
        return session_id in self.sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Elimina una sessione."""
        try:
            if self.use_redis and self.redis_client:
                try:
                    self.redis_client.delete(f"session:{session_id}")
                except Exception:
                    # Fallback
                    if session_id in self.sessions:
                        del self.sessions[session_id]
            elif session_id in self.sessions:
                del self.sessions[session_id]
            
            return True
        except Exception:
            return False


# Istanza globale del gestore di stato
state_manager = StateManager(use_redis=False)  # Per ora senza Redis
