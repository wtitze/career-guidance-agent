"""
Agente AI per l'orientamento basato sulla nuova libreria google-generativeai.
"""
import os
import json
from typing import Dict, Any, Optional, Tuple, List
import google.generativeai as genai
from .web_searcher import WebSearcher
from google.generativeai import types
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Import relativi (unici) per evitare caricamenti multipli del modulo
from .student_profile import StudentProfile
from .state_manager import state_manager

class GeminiOrientationAgent:
    """Agente di orientamento che usa la nuova libreria google-genai."""
    
    def __init__(self):
        # Configura il client CON l'API Key esplicita
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("⚠️  Configura GEMINI_API_KEY nel file .env")
        
        # Configurazioni
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))
        
        try:
            # Configura API key
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            # Stampa solo una volta al primo caricamento
            import sys
            if 'pytest' not in sys.modules and '--reload' not in ' '.join(sys.argv):
                print(f"✅ Agente Gemini inizializzato con {self.model_name}")
        except Exception as e:
            raise ValueError(f"❌ Errore: {e}")
    
    def process_message(self, session_id: str, user_message: str) -> Tuple[str, StudentProfile]:
        """
        Processa un messaggio dello studente e restituisce la risposta dell'agente.
        LOGICA OTTIMIZZATA: Fa TUTTO in una sola richiesta Gemini (estrazione + generazione)
        """
        # 1. Recupera o crea il profilo
        profile = state_manager.get_session(session_id)
        if not profile:
            profile = state_manager.create_session()
            session_id = profile.session_id
        
        # 2. Aggiungi il messaggio utente alla cronologia
        profile.add_conversation_turn("user", user_message)
        
        # 3. UNA SOLA RICHIESTA GEMINI: Estrai info E genera risposta
        response, updated_fields = self._process_message_unified(profile, user_message)
        
        if updated_fields:
            print(f"📝 Info estratte: {updated_fields}")
        
        # 4. Aggiungi la risposta dell'agente alla cronologia
        profile.add_conversation_turn("agent", response)
        
        # 5. Salva il profilo aggiornato
        state_manager.update_session(session_id, profile)
        
        return response, profile
    
    def _process_message_unified(self, profile: StudentProfile, user_message: str) -> Tuple[str, List[str]]:
        """
        OTTIMIZZAZIONE PER QUOTA: Fa TUTTO in una sola richiesta Gemini.
        Estrae info dal messaggio, aggiorna il profilo internamente, E genera la risposta.
        Restituisce (risposta, lista_campi_aggiornati).
        """
        from datetime import datetime
        import re
        
        context = self._build_profile_context(profile, user_message)
        # Quick heuristic update to capture explicit answers (avoid repeated questions)
        try:
            quick_updates = self._heuristic_quick_update(profile, user_message)
            if quick_updates:
                for f in quick_updates:
                    print(f"🔎 Heuristic update applied: {f}")
        except Exception as e:
            print(f"⚠️ Heuristic update failed: {e}")
        
        # Prompt UNIFICATO che fa estrazione E generazione in una sola richiesta
        prompt = f"""ISTRUZIONI CRITICHE: Stai analizzando un messaggio di studente. Devi CONTEMPORANEAMENTE:
1. ESTRARRE informazioni dal messaggio per aggiornare il profilo
2. AGGIORNARE il profilo con i dati estratti
3. GENERARE una risposta appropriata

=== PROFILO ATTUALE ===
{context}

=== MESSAGGIO STUDENTE ===
"{user_message}"

=== STEP 1: ESTRAZIONE INFORMAZIONI ===
Cerca nel messaggio:
- Località (es: "abito a Milano")
- Tipo scuola (es: "ho fatto ITI informatica")
- Materie preferite (es: "mi piace programmazione")
- Hobby/interessi (es: "mi piace giocare")
- Obiettivi (es: "voglio lavorare", "voglio università")
- Volontà di educazione terziaria (cerca: "voglio andare a lavorare", "voglio università", "perché università?")

Per OGNI informazione trovata, crea una riga così:
EXTRACT: field_name=valore|confidence=alta/media/bassa

Esempi di output di estrazione:
EXTRACT: location=Milano|confidence=alta
EXTRACT: wants_tertiary_education=false|confidence=alta
EXTRACT: favorite_subjects=programmazione|confidence=alta

Se NON trovi info rilevanti, non scrivere nulla per lo step 1.

=== STEP 2: GENERAZIONE RISPOSTA ===
Dopo l'estrazione, GENERA UNA RISPOSTA APPROPRIATA:

SE il profilo è INCOMPLETO (< 60% completamento):
- Fai UNA sola domanda naturale per raccogliere l'info più importante che manca
- Scegli tra: location, school_type, favorite_subjects, primary_goal, wants_tertiary_education
- Esempi: "Dove vivi attualmente?", "Che tipo di diploma hai fatto?", "Mi piaci dirmi cosa ti appassiona?"

SE il profilo è COMPLETO (>= 60%) E vuole UNIVERSITÀ:
- Dai consigli su corsi universitari/ITS
- Suggerisci 2-3 percorsi basati su interessi

SE il profilo è COMPLETO E vuole LAVORARE (wants_tertiary_education=false):
- Dai consigli pratici per entrare nel mercato del lavoro
- Suggerisci tirocini, portfolio building, entry-level jobs
- Supporta questa scelta

=== OUTPUT FINALE ===
Formatta ESATTAMENTE così:

EXTRACT: [lista delle info estratte, se ce ne sono]
RESPONSE: [La risposta completa all'utente]"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1500
                )
            )
            
            response_text = response.text.strip()
            print(f"🤖 Raw Gemini output:\n{response_text[:200]}...\n")
            
            # Parsa output
            updated_fields = []
            final_response = ""
            
            # Estrai sezioni EXTRACT e RESPONSE
            extract_lines = []
            for line in response_text.split('\n'):
                if line.startswith('EXTRACT:'):
                    extract_lines.append(line.replace('EXTRACT:', '').strip())
                elif line.startswith('RESPONSE:'):
                    final_response = line.replace('RESPONSE:', '').strip()
                elif final_response:  # Se abbiamo già iniziato RESPONSE, tutto il resto è parte della risposta
                    final_response += '\n' + line
            
            # Processa le linee di estrazione
            for extract_line in extract_lines:
                # Supporta sia linee con '|' sia semplici 'field=value'
                if not extract_line:
                    continue

                parts = extract_line.split('|')
                field_value = parts[0].strip()  # es: "location=Milano" o "hobby=videogiochi"
                confidence = 'alta'

                if '=' in field_value:
                    field_name, value = field_value.split('=', 1)
                    field_name = field_name.strip().lower()
                    value = value.strip()

                    # Estrai confidence se presente
                    for part in parts[1:]:
                        if 'confidence=' in part:
                            confidence = part.split('=')[1].strip().lower()
                            break

                    # Normalizza nomi campi comuni
                    field_map = {
                        'hobby': 'hobbies',
                        'hobbies': 'hobbies',
                        'interest': 'favorite_subjects',
                        'interests': 'favorite_subjects',
                        'favorite_subject': 'favorite_subjects',
                        'favorite_subjects': 'favorite_subjects',
                        'skills': 'favorite_subjects',
                        'language': 'favorite_subjects',
                        'languages': 'favorite_subjects',
                        'programming': 'favorite_subjects',
                        'location': 'location',
                        'city': 'location',
                        'città': 'location',
                        'school_type': 'school_type',
                        'scuola': 'school_type',
                        'diploma': 'school_type',
                        'istituto': 'school_type',
                        'primary_goal': 'primary_goal',
                        'goal': 'primary_goal',
                        'wants_tertiary_education': 'wants_tertiary_education'
                    }

                    mapped_field = field_map.get(field_name, field_name)

                    # Converti valori booleani
                    if isinstance(value, str):
                        low = value.lower()
                        if low in ['true', 'sì', 'si', 'vero', 'yes', '1']:
                            value = True
                        elif low in ['false', 'no', 'falso', '0']:
                            value = False

                    # Verifica che il campo normalizzato esista sul profilo
                    if not hasattr(profile, mapped_field):
                        print(f"⚠️  Campo non riconosciuto dall'estrazione: {mapped_field}, ignoro")
                        continue

                    # Aggiorna profilo in modo sicuro
                    try:
                        # Per campi lista, se il valore contiene virgole, splitta
                        if mapped_field in ['favorite_subjects', 'hobbies', 'disliked_subjects', 'soft_skills'] and isinstance(value, str):
                            items = [v.strip() for v in value.replace(';', ',').split(',') if v.strip()]
                            updated_any = False
                            for item in items:
                                if self._update_profile_field(profile, {
                                    "field_name": mapped_field,
                                    "value": item,
                                    "confidence": confidence
                                }):
                                    updated_any = True
                                    if mapped_field not in updated_fields:
                                        updated_fields.append(mapped_field)
                                    print(f"✅ Estratto: {mapped_field}+= {item}")
                            if not updated_any:
                                # Prova ad aggiornare come singolo valore
                                if self._update_profile_field(profile, {"field_name": mapped_field, "value": value, "confidence": confidence}):
                                    updated_fields.append(mapped_field)
                                    print(f"✅ Estratto: {mapped_field}={value}")
                        else:
                            if self._update_profile_field(profile, {
                                "field_name": mapped_field,
                                "value": value,
                                "confidence": confidence
                            }):
                                updated_fields.append(mapped_field)
                                print(f"✅ Estratto: {mapped_field}={value}")
                    except Exception as upd_e:
                        print(f"⚠️ Errore aggiornamento campo estratto {mapped_field}: {upd_e}")
            
            # Se non c'è una RESPONSE, fallback
            if not final_response:
                if profile.is_sufficient_for_search():
                    if profile.wants_tertiary_education is False:
                        final_response = "Perfetto! Ti supporto nel tuo percorso lavorativo. Raccomandazioni: costruisci un forte portfolio di progetti, partecipa a competizioni, cerca tirocini in aziende software."
                    else:
                        final_response = "Basandomi sui tuoi interessi, considero corsi universitari in informatica/ingegneria informatica."
                else:
                    final_response = "Dimmi di più sui tuoi obiettivi per darti consigli personalizzati."
            
            return final_response, updated_fields
            
        except Exception as e:
            print(f"❌ Errore estrazione unificata: {e}")
            return "Mi scusi, ho avuto un problema. Puoi riprovare?", []
    
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
   - Volontà di fare università/ITS (cerca frasi come "voglio andare a lavorare", "voglio università", "vorrei uno ITS", "perché università?")
   - Vincoli/preferenze (es: "non posso spostarmi", "preferisco pubblico")

2. Per ogni informazione trovata, formatta come JSON:
{{
  "field_name": "nome_campo",
  "value": "valore_estratto",
  "confidence": "alta/media/bassa"
}}

CAMPI SPECIALI:
- Se sente "voglio andare a lavorare" o "voglio lavorare" → {{"field_name": "wants_tertiary_education", "value": false, "confidence": "alta"}}
- Se sente "voglio università" o "voglio studiare" → {{"field_name": "wants_tertiary_education", "value": true, "confidence": "alta"}}
- Se sente "perché devo fare università?" o "non voglio università" → {{"field_name": "wants_tertiary_education", "value": false, "confidence": "alta"}}
- Se sente "voglio uno ITS" → {{"field_name": "wants_tertiary_education", "value": true, "confidence": "alta"}} e {{"field_name": "institution_preference", "value": "ITS", "confidence": "alta"}}

3. Se non trovi informazioni rilevanti, rispondi solo con: {{}}

Esempi:
- Input: "Abito a Bologna" → {{"field_name": "location", "value": "Bologna", "confidence": "alta"}}
- Input: "Studio al liceo scientifico" → {{"field_name": "school_type", "value": "Liceo Scientifico", "confidence": "alta"}}
- Input: "Mi piace la matematica" → {{"field_name": "favorite_subjects", "value": "matematica", "confidence": "alta"}}
- Input: "Voglio andare a lavorare" → {{"field_name": "wants_tertiary_education", "value": false, "confidence": "alta"}}

Rispondi SOLO con il JSON, senza altro testo."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Bassa per estrazione precisa
                    max_output_tokens=500
                )
            )
            
            # Prova a parsare la risposta come JSON
            response_text = response.text.strip()
            # print(f"DEBUG: Risposta estrazione Gemini: {response_text}")
        
            # PULIZIA con regex
            import re
            # 1. Rimuovi backticks semplici
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            # 2. Regex per estrarre solo il JSON
            json_pattern = r'(\[.*\]|\{.*\})'
            match = re.search(json_pattern, response_text, re.DOTALL)
            if match:
                response_text = match.group(1).strip()
            
            # DEBUG (puoi rimuoverlo dopo)
            # print(f"🔍 JSON pulito: {response_text[:100]}...")
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
                    
                    # print(f"DEBUG: Campi aggiornati: {updated_fields}")
                    # print(f"DEBUG: Location profilo: {profile.location}")
                            
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON non valido da Gemini: {response_text}")
                    print(f"   Errore: {e}")
                    
                    return updated_fields
                    
        except Exception as e:
            print(f"⚠️  Errore nell'estrazione info: {e}")
            return []

    def _heuristic_quick_update(self, profile: StudentProfile, user_message: str) -> List[str]:
        """Aggiornamenti rapidi e locali basati su pattern semplici nel messaggio.
        Serve a catturare risposte dirette (es. 'diploma in informatica', 'voglio lavorare')
        prima della chiamata al modello, per evitare domande ripetute.
        Restituisce la lista dei campi aggiornati.
        """
        updated = []
        msg = user_message.lower()

        # Rileva volontà di entrare nel mondo del lavoro
        if any(p in msg for p in ["voglio lavorare", "entrare nel mondo del lavoro", "vorrei lavorare", "preferisco lavorare", "andare a lavorare", "lavorare"]):
            if self._update_profile_field(profile, {"field_name": "wants_tertiary_education", "value": False, "confidence": "alta"}):
                updated.append("wants_tertiary_education")

        # Rileva dichiarazioni di voler studiare
        if any(p in msg for p in ["voglio studiare", "andare all'università", "università", "its"]):
            if self._update_profile_field(profile, {"field_name": "wants_tertiary_education", "value": True, "confidence": "alta"}):
                updated.append("wants_tertiary_education")

        # Rileva diploma / scuola
        # Cerca frasi tipo 'diploma in informatica' o 'ho fatto l'iti', 'galvani'
        if any(p in msg for p in ["diplom", "ho fatto", "ho appena finito", "sono diplomato", "diploma in", "galvani", "istituto", "itis", "iti", "tecnico"]):
            # prova estrarre substring rilevante
            import re
            m = re.search(r"(diploma(?: di)?|sono diplomato(?: in)?|ho fatto l'|ho fatto )\s*([a-zA-Z0-9\s\,\-\'\.]{2,50})", user_message, re.IGNORECASE)
            school_val = None
            if m and len(m.groups()) >= 2:
                school_val = m.group(2).strip()
            else:
                # fallback: prendi parole chiave come 'informatica'
                for kw in ["informatica", "elettronica", "meccanica", "chimica"]:
                    if kw in msg and not profile.school_type:
                        school_val = kw
                        break

            if school_val:
                if self._update_profile_field(profile, {"field_name": "school_type", "value": school_val, "confidence": "alta"}):
                    updated.append("school_type")

        # Rileva competenze/languages/programming
        if any(kw in msg for kw in ["python", "c++", "java", "c#", "javascript", "js"]):
            langs = []
            for kw in ["python", "c++", "java", "c#", "javascript", "js"]:
                if kw in msg:
                    langs.append(kw)
            for lang in langs:
                if self._update_profile_field(profile, {"field_name": "favorite_subjects", "value": lang, "confidence": "alta"}):
                    if "favorite_subjects" not in updated:
                        updated.append("favorite_subjects")

        # Rileva obiettivi professionali in modo generico (es. "vorrei lavorare come X", "voglio diventare Y")
        import re
        goal_patterns = [
            r"vorrei lavorare come ([a-zA-Z0-9'\-\s]+)",
            r"voglio lavorare come ([a-zA-Z0-9'\-\s]+)",
            r"vorrei diventare ([a-zA-Z0-9'\-\s]+)",
            r"voglio diventare ([a-zA-Z0-9'\-\s]+)",
            r"mi piacerebbe essere ([a-zA-Z0-9'\-\s]+)",
            r"mi piacerebbe lavorare come ([a-zA-Z0-9'\-\s]+)",
            r"lavorare come ([a-zA-Z0-9'\-\s]+)",
        ]
        goal_found = None
        for pat in goal_patterns:
            m = re.search(pat, msg)
            if m:
                candidate = m.group(1).strip()
                candidate = re.sub(r"[\.,;!\n].*$", "", candidate).strip()
                # Trim trailing conjunction phrases and clauses (e.g., 'e', 'con', 'ma', 'per', 'che')
                candidate = re.split(r"\s+(?:e|con|ma|per|che)\s+", candidate, 1)[0].strip()
                goal_found = candidate
                break

        if goal_found:
            if self._update_profile_field(profile, {"field_name": "primary_goal", "value": goal_found, "confidence": "alta"}):
                if "primary_goal" not in updated:
                    updated.append("primary_goal")
        else:
            # Se l'utente esprime volontà di lavorare ma non specifica ruolo, registra un goal generico
            if any(p in msg for p in ["voglio lavorare", "vorrei lavorare", "preferisco lavorare", "andare a lavorare", "lavorare"]):
                if self._update_profile_field(profile, {"field_name": "primary_goal", "value": "occupazione", "confidence": "media"}):
                    if "primary_goal" not in updated:
                        updated.append("primary_goal")

        # Rileva località semplice
        if any(city in msg for city in ["milano", "roma", "bologna", "torino", "napoli"]):
            for city in ["milano", "roma", "bologna", "torino", "napoli"]:
                if city in msg and (not profile.location or 'non specificata' in str(profile.location).lower()):
                    if self._update_profile_field(profile, {"field_name": "location", "value": city.capitalize(), "confidence": "alta"}):
                        updated.append("location")

        return updated
    
    def _update_profile_field(self, profile: StudentProfile, data: Dict) -> bool:
        """Aggiorna un campo del profilo con i dati estratti."""
        if not data or "field_name" not in data or "value" not in data:
            return False
        
        field_name = data["field_name"]
        value = data["value"]
        confidence = data.get("confidence", "media")
        
        # Mappa i campi speciali (liste)
        list_fields = ["favorite_subjects", "hobbies", "disliked_subjects", "soft_skills"]
        
        # Campi booleani
        boolean_fields = ["wants_tertiary_education", "willing_to_relocate", "further_studies"]
        
        # Import datetime
        from datetime import datetime
        
        try:
            if field_name in list_fields:
                # Per campi lista, aggiungi il valore alla lista esistente
                current_list = getattr(profile, field_name, [])
                # Se value è stringa contenente virgole, splitta
                if isinstance(value, str) and (',' in value or ';' in value):
                    items = [v.strip() for v in value.replace(';', ',').split(',') if v.strip()]
                    changed = False
                    for item in items:
                        if item not in current_list:
                            current_list.append(item)
                            changed = True
                    if changed:
                        setattr(profile, field_name, current_list)
                        profile.last_updated = datetime.now()
                        profile._update_completeness()
                        return True
                else:
                    if value not in current_list:
                        current_list.append(value)
                        setattr(profile, field_name, current_list)
                        profile.last_updated = datetime.now()
                        profile._update_completeness()
                        return True
            elif field_name in boolean_fields:
                # Per campi booleani, converti il valore se necessario
                bool_value = value if isinstance(value, bool) else str(value).lower() in ['true', '1', 'yes', 'sì', 'vero']
                current_value = getattr(profile, field_name, None)
                if current_value is None or confidence == "alta":
                    setattr(profile, field_name, bool_value)
                    profile.last_updated = datetime.now()
                    profile._update_completeness()
                    return True
            else:
                # Per campi singoli
                current_value = getattr(profile, field_name, None)
                if not current_value or confidence == "alta":
                    setattr(profile, field_name, value)
                    profile.last_updated = datetime.now()
                    profile._update_completeness()
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
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
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
        """Genera una risposta con raccomandazioni BASATE SU RICERCA WEB."""
        
        # VERIFICA IMPORTANTE: Se lo studente NON vuole educazione terziaria, dai consigli per lavoro
        if profile.wants_tertiary_education is False:
            return self._generate_work_path_response(profile, user_message)
        
        # Se è indeciso, continua con la ricerca di università
        # 1. Inizializza web searcher
        if not hasattr(self, 'web_searcher'):
            self.web_searcher = WebSearcher()
        
        # 2. Cerca informazioni reali sul web
        profile_data = {
            "favorite_subjects": profile.favorite_subjects,
            "location": profile.location,
            "school_type": profile.school_type,
            "primary_goal": profile.primary_goal,
            "institution_preference": profile.institution_preference
        }
        
        print(f"🔍 Avvio ricerca web per: {profile_data["favorite_subjects"]} a {profile_data["location"]}")
        
        try:
            search_results = self.web_searcher.search_for_student_profile(profile_data)
            has_web_results = (search_results["university_courses"]["university_results"] > 0 or 
                              search_results["its_courses"]["its_results"] > 0)
        except Exception as e:
            print(f"⚠️  Errore ricerca web: {e}")
            search_results = {}
            has_web_results = False
        
        # 3. Costruisci il contesto
        context = self._build_profile_context(profile, user_message)
        
        # 4. Prompt diverso se abbiamo risultati web
        if has_web_results:
            prompt = f"""Sei un orientatore universitario ESPERTO. Hai informazioni AGGIORNATE dal web.

PROFILO STUDENTE:
{context}

RISULTATI RICERCA WEB:"""
            
            # Aggiungi risultati università
            uni_courses = search_results.get("university_courses", {}).get("courses", [])
            if uni_courses:
                prompt += "\n📚 CORSI UNIVERSITARI TROVATI:\n"
                for i, course in enumerate(uni_courses[:2], 1):
                    prompt += f"{i}. {course["name"]} - {course.get("university", "università")}\n"
                    if course.get("snippet"):
                        prompt += f"   Info: {course["snippet"]}\n"
            
            # Aggiungi risultati ITS
            its_courses = search_results.get("its_courses", {}).get("courses", [])
            if its_courses:
                prompt += "\n🔧 CORSI ITS TROVATI:\n"
                for i, course in enumerate(its_courses[:2], 1):
                    prompt += f"{i}. {course["name"][:80]}...\n"
                    if course.get("duration"):
                        prompt += f"   Durata: {course["duration"]}\n"
            
            prompt += """

BASANDOTI SUL PROFILO DELLO STUDENTE E SUI RISULTATI REALI TROVATI:
1. Fornisci un riepilogo PERSONALIZZATO
2. Suggerisci 2-3 percorsi CONCRETI
3. Includi CONSIGLI PRATICI

Sii INCORAGGIANTE, PROFESSIONALE e BASATO SUI DATI REALI."""
        
        else:
            # Fallback: prompt senza risultati web
            prompt = f"""Sei un orientatore universitario.

{context}

Il profilo è completo al {profile.profile_completeness*100:.1f}%.

FORNISCI:
1. Un breve riepilogo del profilo
2. 2-3 possibili aree di studio
3. Consigli per i prossimi passi

Sii incoraggiante e professionale."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=1000
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ Errore Gemini (raccomandazioni): {e}")
            return "Grazie per le informazioni! Ho analizzato il tuo profilo. Considera di consultare i siti ufficiali delle università per informazioni aggiornate sui corsi."
    
    def _generate_work_path_response(self, profile: StudentProfile, user_message: str) -> str:
        """Genera consigli per chi vuole andare a lavorare direttamente (senza università)."""
        context = self._build_profile_context(profile, user_message)
        
        prompt = f"""Sei un orientatore professionale esperto nel job placement.

{context}

Lo studente ha CHIARAMENTE ESPRESSO che vuole andare a LAVORARE, non fare università o ITS.

BASANDOTI SU QUESTO:
1. Riconosci e rispetta questa scelta
2. Fornisci 3-4 PERCORSI CONCRETI per entrare nel mondo del lavoro:
   - Tirocini/Apprendistato in aziende software/gaming
   - Programmi di entry-level in aziende tech
   - Freelancing e portfolio building
   - Competizioni e certazioni nel settore
3. Includi STRATEGIE PRATICHE:
   - Come costruire un portfolio
   - Quale certificazioni considerare
   - Come fare networking nel settore
   - Siti/piattaforme per trovare lavoro
4. Dai CONSIGLI SPECIFICI per {profile.location or 'la sua città'}

Sii INCORAGGIANTE e supporta questa scelta di inserimento veloce nel mercato del lavoro.
Ricordagli che può sempre tornare a studiare in seguito se lo desidera."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=1000
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ Errore Gemini (work path): {e}")
            return "Perfetto! Ti supporto nel tuo percorso lavorativo. Raccomandazioni: costruisci un forte portfolio di progetti, partecipa a competizioni di game development, cerca tirocini in aziende software rinomate, e considera certificazioni professionali nel settore."
    def _build_profile_context(self, profile: StudentProfile, last_message: str = "") -> str:
        """Costruisce il contesto del profilo per Gemini."""
        wants_tertiary = "Non specificato"
        if profile.wants_tertiary_education is True:
            wants_tertiary = "Sì (università/ITS)"
        elif profile.wants_tertiary_education is False:
            wants_tertiary = "No (vuole lavorare)"
        
        context_lines = [
            "=== PROFILO STUDENTE ===",
            f"Completamento: {profile.profile_completeness*100:.1f}%",
            f"Località: {profile.location or 'Non specificata'}",
            f"Tipo scuola: {profile.school_type or 'Non specificato'}",
            f"Materie preferite: {', '.join(profile.favorite_subjects) or 'Nessuna'}",
            f"Hobby: {', '.join(profile.hobbies) or 'Nessuno'}",
            f"Obiettivo principale: {profile.primary_goal or 'Non specificato'}",
            f"Vuole educazione terziaria: {wants_tertiary}",
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

# Istanza globale - lazy loaded
_orientation_agent = None

def get_orientation_agent():
    """Getter lazy-loading per l'agente (evita inizializzazioni multiple)."""
    global _orientation_agent
    if _orientation_agent is None:
        try:
            _orientation_agent = GeminiOrientationAgent()
        except ValueError as e:
            print(f"⚠️  {e}")
            _orientation_agent = None
    return _orientation_agent

# Alias per compatibilità retroattiva
@property
def orientation_agent():
    return get_orientation_agent()

# Prova a inizializzare solo una volta al startup
try:
    orientation_agent = get_orientation_agent()
except:
    orientation_agent = None
