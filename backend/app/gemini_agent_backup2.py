"""
Agente AI per l'orientamento basato sulla nuova libreria google-genai.
"""
import os
from typing import Dict, Any, Optional, Tuple
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Import assoluti invece che relativi
try:
    from student_profile import StudentProfile
    from state_manager import state_manager
except ImportError:
    # Fallback per quando viene eseguito da directory diversa
    from .student_profile import StudentProfile
    from .state_manager import state_manager

class GeminiOrientationAgent:
    """Agente di orientamento che usa la nuova libreria google-genai."""
    
    def __init__(self):
        # Configura il client CON l'API Key esplicita
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key or api_key == "your_api_key_here":
            raise ValueError("⚠️  Configura GEMINI_API_KEY nel file .env")
        
        try:
            # NUOVA SINTASSI: Passa api_key direttamente al client
            self.client = genai.Client(api_key=api_key)
            print(f"✅ Agente Gemini inizializzato")
        except Exception as e:
            raise ValueError(f"❌ Errore: {e}")
        
        # Configurazioni
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))
    
    def process_message(self, session_id: str, user_message: str) -> Tuple[str, StudentProfile]:
        """Processa un messaggio dello studente."""
        profile = state_manager.get_session(session_id)
        if not profile:
            profile = state_manager.create_session()
            session_id = profile.session_id
        
        profile.add_conversation_turn("user", user_message)
        
        if profile.is_sufficient_for_search():
            response = self._generate_recommendation_response(profile, user_message)
        else:
            response = self._generate_profile_question(profile, user_message)
        
        profile.add_conversation_turn("agent", response)
        state_manager.update_session(session_id, profile)
        
        return response, profile
    
    def _generate_profile_question(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una domanda per completare il profilo."""
        context = self._build_profile_context(profile, user_message)
        
        prompt = f"""Sei un orientatore universitario.

{context}

Analizza e formula UNA sola domanda naturale per raccogliere l'informazione più importante mancante.

La tua risposta deve essere SOLO la domanda, senza spiegazioni."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=500
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ Errore Gemini: {e}")
            if not profile.location:
                return "Dove vivi?"
            elif not profile.school_type:
                return "Che scuola frequenti?"
            else:
                return "Quali materie ti piacciono?"
    
    def _generate_recommendation_response(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una risposta con raccomandazioni."""
        context = self._build_profile_context(profile, user_message)
        
        prompt = f"""Sei un orientatore universitario.

{context}

Fornisci un breve riepilogo e 2-3 possibili percorsi."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=800
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ Errore Gemini: {e}")
            return "Grazie per le informazioni! Sto analizzando il tuo profilo."
    
    def _build_profile_context(self, profile: StudentProfile, last_message: str = "") -> str:
        """Costruisce il contesto del profilo."""
        context_lines = [
            "=== PROFILO STUDENTE ===",
            f"Località: {profile.location or 'Non specificata'}",
            f"Scuola: {profile.school_type or 'Non specificata'}",
            f"Materie preferite: {', '.join(profile.favorite_subjects) or 'Nessuna'}",
            f"Obiettivo: {profile.primary_goal or 'Non specificato'}",
        ]
        
        return "\n".join(context_lines)
    
    def start_new_conversation(self) -> Tuple[str, StudentProfile]:
        """Inizia una nuova conversazione."""
        profile = state_manager.create_session()
        welcome_message = "Ciao! Sono il tuo orientatore virtuale. Dove vivi attualmente?"
        
        profile.add_conversation_turn("agent", welcome_message)
        state_manager.update_session(profile.session_id, profile)
        
        return welcome_message, profile

# Istanza globale
try:
    orientation_agent = GeminiOrientationAgent()
except ValueError as e:
    print(f"⚠️  {e}")
    orientation_agent = None
