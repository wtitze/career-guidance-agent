"""
Agente AI per l'orientamento basato sulla nuova libreria google-genai.
Versione con estrazione funzionante.
"""
import os
import json
from typing import Dict, Any, Optional, Tuple, List
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime

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
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))
    
    def process_message(self, session_id: str, user_message: str) -> Tuple[str, StudentProfile]:
        """Processa un messaggio dello studente e restituisce la risposta dell'agente."""
        # 1. Recupera o crea il profilo
        profile = state_manager.get_session(session_id)
        if not profile:
            profile = state_manager.create_session()
            session_id = profile.session_id
        
        # 2. Aggiungi il messaggio utente alla cronologia
        profile.add_conversation_turn("user", user_message)
        
        # 3. FASE DI ESTRAZIONE: Analizza il messaggio per aggiornare il profilo
        updated_fields = self._extract_profile_info_simple(profile, user_message)
        
        if updated_fields:
            print(f"📝 Info estratte: {updated_fields}")
        
        # 4. Determina l'azione basata sul profilo AGGIORNATO
        if profile.is_sufficient_for_search():
            response = self._generate_recommendation_response(profile, user_message)
        else:
            response = self._generate_profile_question(profile, user_message)
        
        # 5. Aggiungi la risposta dell'agente alla cronologia
        profile.add_conversation_turn("agent", response)
        
        # 6. Salva il profilo aggiornato
        state_manager.update_session(session_id, profile)
        
        return response, profile
    
    def _extract_profile_info_simple(self, profile: StudentProfile, user_message: str) -> List[str]:
        """Versione semplificata e funzionante dell'estrazione."""
        prompt = f'''Analizza questo messaggio: "{user_message}"

Estrai SOLO informazioni per questi campi specifici:
1. location (es: "Roma", "Milano", "Bologna")
2. school_type (es: "Liceo Scientifico", "ITIS Informatica", "Liceo Classico")
3. favorite_subjects (es: "matematica", "fisica", "informatica")
4. hobbies (es: "programmazione", "sport", "musica")
5. primary_goal (es: "lavoro", "università", "formazione pratica")
6. institution_preference (es: "pubblico", "privato")
7. willing_to_relocate (TRUE/FALSE per "disponibile a trasferirsi")

Formato di risposta SOLO JSON:
[
  {{"field_name": "nome_campo", "value": "valore", "confidence": "alta"}}
]

Se non trovi info, rispondi con: []

Esempi:
- "Abito a Milano" → [{{"field_name": "location", "value": "Milano", "confidence": "alta"}}]
- "Studio al liceo" → [{{"field_name": "school_type", "value": "Liceo", "confidence": "media"}}]
- "Mi piace la matematica" → [{{"field_name": "favorite_subjects", "value": "matematica", "confidence": "alta"}}]'''
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=500
                )
            )
            
            # Pulisci la risposta
            response_text = response.text.strip()
            # Rimuovi possibili backticks
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            if response_text.lower().startswith('json'):
                response_text = response_text[4:].strip()
            
            updated_fields = []
            
            if response_text and response_text != "[]":
                try:
                    data = json.loads(response_text)
                    if isinstance(data, list):
                        for item in data:
                            if self._update_profile_field(profile, item):
                                updated_fields.append(item.get("field_name", "unknown"))
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON non valido: {response_text}")
                    print(f"   Errore: {e}")
            
            return updated_fields
            
        except Exception as e:
            print(f"⚠️  Errore estrazione: {e}")
            return []
    
    def _update_profile_field(self, profile: StudentProfile, data: Dict) -> bool:
        """Aggiorna un campo del profilo con i dati estratti."""
        if not data or "field_name" not in data or "value" not in data:
            return False
        
        field_name = data["field_name"]
        value = data["value"]
        
        # Normalizza i nomi dei campi
        field_map = {
            "località": "location",
            "location": "location",
            "scuola": "school_type", 
            "school_type": "school_type",
            "materie": "favorite_subjects",
            "favorite_subjects": "favorite_subjects",
            "interessi": "hobbies",
            "hobbies": "hobbies",
            "obiettivo": "primary_goal",
            "primary_goal": "primary_goal"
        }
        
        normalized_field = field_map.get(field_name.lower(), field_name)
        
        try:
            # Campi lista
            list_fields = ["favorite_subjects", "hobbies", "disliked_subjects", "soft_skills"]
            
            if normalized_field in list_fields:
                current = getattr(profile, normalized_field, [])
                if value not in [v.lower() for v in current]:
                    current.append(value)
                    setattr(profile, normalized_field, current)
                    profile._update_completeness()
                    return True
            else:
                # Campi singoli
                setattr(profile, normalized_field, value)
                profile._update_completeness()
                return True
                
        except AttributeError:
            print(f"⚠️  Campo non valido: {normalized_field}")
        
        return False
    
    def _generate_profile_question(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una domanda per completare il profilo."""
        context = self._build_profile_context(profile, user_message)
        
        prompt = f'''Sei un orientatore universitario.

Profilo attuale:
{context}

BASANDOTI sull'ultimo messaggio, fai UNA sola domanda per ottenere l'informazione più importante che manca.

La tua risposta deve essere SOLO la domanda.'''
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=200
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
                return "Cosa ti piacerebbe fare dopo il diploma?"
    
    def _generate_recommendation_response(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una risposta con raccomandazioni."""
        context = self._build_profile_context(profile, user_message)
        
        prompt = f'''Sei un orientatore universitario.

Profilo studente:
{context}

Dai un breve riepilogo e suggerisci 2-3 aree di studio o formazione che potrebbero interessare.'''
        
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
            return "Grazie per le informazioni! Analizzo il tuo profilo."
    
    def _build_profile_context(self, profile: StudentProfile, last_message: str = "") -> str:
        """Costruisce il contesto del profilo."""
        return f"""Completamento: {profile.profile_completeness*100:.1f}%
Località: {profile.location or 'Non specificata'}
Scuola: {profile.school_type or 'Non specificata'}
Materie preferite: {', '.join(profile.favorite_subjects) or 'Nessuna'}
Obiettivo: {profile.primary_goal or 'Non specificato'}"""
    
    def start_new_conversation(self) -> Tuple[str, StudentProfile]:
        """Inizia una nuova conversazione."""
        profile = state_manager.create_session()
        welcome_message = "Ciao! Sono il tuo orientatore. Dove vivi?"
        
        profile.add_conversation_turn("agent", welcome_message)
        state_manager.update_session(profile.session_id, profile)
        
        return welcome_message, profile

# Istanza globale
try:
    orientation_agent = GeminiOrientationAgent()
except ValueError as e:
    print(f"⚠️  {e}")
    orientation_agent = None
