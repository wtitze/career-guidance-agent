"""
Agente AI per l'orientamento basato sulla nuova libreria google-genai.
"""
import os
import json
from typing import Dict, Any, Optional, Tuple, List
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
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))
    
    def process_message(self, session_id: str, user_message: str) -> Tuple[str, StudentProfile]:
        """
        Processa un messaggio dello studente e restituisce la risposta dell'agente.
        NUOVA LOGICA: 1. Estrai info, 2. Aggiorna profilo, 3. Genera risposta
        """
        # 1. Recupera o crea il profilo
        profile = state_manager.get_session(session_id)
        if not profile:
            profile = state_manager.create_session()
            session_id = profile.session_id
        
        # 2. Aggiungi il messaggio utente alla cronologia
        profile.add_conversation_turn("user", user_message)
        
        # 3. FASE DI ESTRAZIONE: Analizza il messaggio per aggiornare il profilo
        updated_fields = self._extract_profile_info(profile, user_message)
        
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
    
    def _extract_profile_info(self, profile: StudentProfile, user_message: str) -> List[str]:
        """
        Analizza il messaggio dello studente ed estrae informazioni per aggiornare il profilo.
        Restituisce la lista dei campi aggiornati.
        """
        # Costruisci il contesto attuale del profilo
        context = self._build_profile_context(profile, user_message)
        
        prompt = f"""Analizza il messaggio dello studente ed estrai SOLO le informazioni che corrispondono ai campi del profilo.

PROFILO ATTUALMENTE:
{context}

MESSAGGIO STUDENTE: "{user_message}"

INSTRUZIONI:
1. Identifica se nel messaggio ci sono informazioni su:
   - Località/residenza (es: "abito a Roma", "vivo a Milano")
   - Tipo di scuola/diploma (es: "frequento il liceo", "ho fatto l'ITIS")
   - Materie preferite (es: "mi piace matematica", "amo la fisica")
   - Hobby/interessi (es: "mi piace programmare", "gioco a calcio")
   - Obiettivi (es: "vorrei lavorare", "mi interessa l'università")
   - Vincoli/preferenze (es: "non posso spostarmi", "preferisco pubblico")

2. Per ogni informazione trovata, formatta come JSON:
{{
  "field_name": "nome_campo",
  "value": "valore_estratto",
  "confidence": "alta/media/bassa"
}}

3. Se non trovi informazioni rilevanti, rispondi solo con: {{}}

Esempi:
- Input: "Abito a Bologna" → {{"field_name": "location", "value": "Bologna", "confidence": "alta"}}
- Input: "Studio al liceo scientifico" → {{"field_name": "school_type", "value": "Liceo Scientifico", "confidence": "alta"}}
- Input: "Mi piace la matematica" → {{"field_name": "favorite_subjects", "value": "matematica", "confidence": "alta"}}

Rispondi SOLO con il JSON, senza altro testo."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Bassa per estrazione precisa
                    max_output_tokens=500
                )
            )
            
            # Prova a parsare la risposta come JSON
            response_text = response.text.strip()
        # DEBUG: mostra cosa riceviamo
        print("DEBUG - Risposta grezza: " + response_text[:80] + "...")
        
        # PULISCI: rimuovi i backticks 
        response_text = response_text.replace("\", "").strip()
        
        # Rimuovi anche la parola "json" se è all'inizio
        if response_text.lower().startswith("json"):
            response_text = response_text[4:].strip()
        
        print("DEBUG - Dopo pulizia: " + response_text[:80] + "...")
        updated_fields = []
            
            if response_text and response_text != "{}":
                try:
                    # Gestisci sia oggetto singolo che lista
                    if response_text.startswith("["):
                        data = json.loads(response_text)
                        if isinstance(data, list):
                            for item in data:
                                if self._update_profile_field(profile, item):
                                    updated_fields.append(item.get("field_name", "unknown"))
                        else:
                            if self._update_profile_field(profile, data):
                                updated_fields.append(data.get("field_name", "unknown"))
                    else:
                        data = json.loads(response_text)
                        if self._update_profile_field(profile, data):
                            updated_fields.append(data.get("field_name", "unknown"))
                            
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON non valido da Gemini: {response_text}")
                    print(f"   Errore: {e}")
            
            return updated_fields
            
        except Exception as e:
            print(f"⚠️  Errore nell'estrazione info: {e}")
            return []
    
    def _update_profile_field(self, profile: StudentProfile, data: Dict) -> bool:
        """Aggiorna un campo del profilo con i dati estratti."""
        if not data or "field_name" not in data or "value" not in data:
            return False
        
        field_name = data["field_name"]
        value = data["value"]
        confidence = data.get("confidence", "media")
        
        # Mappa i campi speciali (liste)
        list_fields = ["favorite_subjects", "hobbies", "disliked_subjects", "soft_skills"]
        
        try:
            if field_name in list_fields:
                # Per campi lista, aggiungi il valore alla lista esistente
                current_list = getattr(profile, field_name, [])
                if value not in current_list:
                    current_list.append(value)
                    setattr(profile, field_name, current_list)
                    profile.last_updated = os.datetime.now() if hasattr(os, 'datetime') else __import__('datetime').datetime.now()
                    return True
            else:
                # Per campi singoli
                current_value = getattr(profile, field_name, None)
                if not current_value or confidence == "alta":
                    setattr(profile, field_name, value)
                    profile.last_updated = os.datetime.now() if hasattr(os, 'datetime') else __import__('datetime').datetime.now()
                    return True
                    
        except AttributeError:
            print(f"⚠️  Campo non valido: {field_name}")
        
        return False
    
    def _generate_profile_question(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una domanda per completare il profilo."""
        context = self._build_profile_context(profile, user_message)
        
        prompt = f"""Sei un orientatore universitario esperto e paziente.

{context}

Il profilo è completo al {profile.profile_completeness*100:.1f}%.

BASATI SULL'ULTIMO MESSAGGIO DELLO STUDENTE E SUL PROFILO ATTUALE:
1. Qual è l'informazione più importante che manca ancora?
2. Formula UNA sola domanda naturale e amichevole per raccogliere quell'informazione.

ESEMPI:
- Se manca la località: "Per darti consigli mirati, dove vivi attualmente?"
- Se manca il tipo di scuola: "Che scuola superiore stai frequentando?"
- Se mancano interessi: "Quali materie ti piacciono di più a scuola?"

La tua risposta deve essere SOLO la domanda, senza spiegazioni."""
        
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
            print(f"❌ Errore Gemini (domanda): {e}")
            # Fallback basato su cosa manca
            if not profile.location:
                return "Per darti consigli mirati, dove vivi attualmente?"
            elif not profile.school_type:
                return "Che tipo di scuola superiore stai frequentando o hai frequentato?"
            elif not profile.favorite_subjects:
                return "Quali materie ti piacciono di più a scuola o ti hanno interessato di più?"
            else:
                return "Dimmi di più sui tuoi obiettivi dopo il diploma."
    
    def _generate_recommendation_response(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una risposta con raccomandazioni."""
        context = self._build_profile_context(profile, user_message)
        
        prompt = f"""Sei un orientatore universitario. Lo studente ha fornito informazioni sufficienti.

{context}

Il profilo è completo al {profile.profile_completeness*100:.1f}%.

FORNISCI:
1. Un breve riepilogo di ciò che hai capito del profilo (2-3 frasi)
2. 2-3 possibili percorsi che potrebbero interessargli (es: Università, ITS, formazione specifica)
3. Una domanda per approfondire o chiarire qualcosa

Sii incoraggiante, professionale e specifico. Non inventare corsi specifici, ma indica aree generali."""
        
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
            print(f"❌ Errore Gemini (raccomandazioni): {e}")
            return "Grazie per tutte le informazioni! Ho un quadro più chiaro. Potresti dirmi se hai preferenze particolari sul tipo di istituzione (pubblico/privato) o sulla durata degli studi?"
    
    def _build_profile_context(self, profile: StudentProfile, last_message: str = "") -> str:
        """Costruisce il contesto del profilo per Gemini."""
        context_lines = [
            "=== PROFILO STUDENTE ===",
            f"Completamento: {profile.profile_completeness*100:.1f}%",
            f"Località: {profile.location or 'Non specificata'}",
            f"Tipo scuola: {profile.school_type or 'Non specificato'}",
            f"Materie preferite: {', '.join(profile.favorite_subjects) or 'Nessuna'}",
            f"Hobby: {', '.join(profile.hobbies) or 'Nessuno'}",
            f"Obiettivo principale: {profile.primary_goal or 'Non specificato'}",
            f"Preferenza istituzione: {profile.institution_preference or 'Non specificata'}",
            f"Disponibile a trasferirsi: {'Sì' if profile.willing_to_relocate else 'No' if profile.willing_to_relocate is not None else 'Non specificato'}",
        ]
        
        if last_message:
            context_lines.append("")
            context_lines.append(f"=== ULTIMO MESSAGGIO STUDENTE ===")
            context_lines.append(last_message)
        
        return "\n".join(context_lines)
    
    def start_new_conversation(self) -> Tuple[str, StudentProfile]:
        """Inizia una nuova conversazione."""
        profile = state_manager.create_session()
        welcome_message = "Ciao! Sono il tuo orientatore virtuale. Per darti consigli personalizzati, dove vivi attualmente?"
        
        profile.add_conversation_turn("agent", welcome_message)
        state_manager.update_session(profile.session_id, profile)
        
        return welcome_message, profile

# Istanza globale
try:
    orientation_agent = GeminiOrientationAgent()
except ValueError as e:
    print(f"⚠️  {e}")
    orientation_agent = None
