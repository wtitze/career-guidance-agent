import re

with open('gemini_agent.py', 'r') as f:
    content = f.read()

# 1. Aggiungi l'import del web searcher all'inizio della classe
import_pattern = r'from \.student_profile import StudentProfile\nfrom \.state_manager import state_manager'

new_import = '''from .student_profile import StudentProfile
from .state_manager import state_manager
from .web_searcher import WebSearcher'''

content = re.sub(import_pattern, new_import, content)

# 2. Aggiungi il web searcher all'__init__
init_pattern = r'self\.temperature = float\(os\.getenv\("AGENT_TEMPERATURE", 0\.7\)\)'

new_init = '''self.temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))
        self.web_searcher = WebSearcher()  # Per ricerche web'''

content = re.sub(init_pattern, new_init, content)

# 3. Aggiorna _generate_recommendation_response per usare il web searcher
method_pattern = r'def _generate_recommendation_response\(self, profile: StudentProfile, user_message: str\) -> str:.*?def _build_profile_context'

new_method = '''def _generate_recommendation_response(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una risposta con raccomandazioni BASATE SU RICERCA WEB."""
        # 1. Cerca informazioni reali sul web
        profile_data = {
            "favorite_subjects": profile.favorite_subjects,
            "location": profile.location,
            "school_type": profile.school_type,
            "primary_goal": profile.primary_goal,
            "institution_preference": profile.institution_preference
        }
        
        print(f"🔍 Avvio ricerca web per profilo: {profile_data['favorite_subjects']} a {profile_data['location']}")
        
        try:
            search_results = self.web_searcher.search_for_student_profile(profile_data)
            has_web_results = (search_results["university_courses"]["university_results"] > 0 or 
                              search_results["its_courses"]["its_results"] > 0)
        except Exception as e:
            print(f"⚠️  Errore ricerca web: {e}")
            search_results = {}
            has_web_results = False
        
        # 2. Costruisci il contesto
        context = self._build_profile_context(profile, user_message)
        
        # 3. Prompt diverso se abbiamo risultati web
        if has_web_results:
            prompt = f"""Sei un orientatore universitario ESPERTO. Hai informazioni AGGIORNATE dal web.

PROFILO STUDENTE:
{context}

RISULTATI RICERCA WEB:
"""
            
            # Aggiungi risultati università
            uni_courses = search_results.get("university_courses", {}).get("courses", [])
            if uni_courses:
                prompt += "\\n📚 CORSI UNIVERSITARI TROVATI:\\n"
                for i, course in enumerate(uni_courses[:2], 1):
                    prompt += f"{i}. {course['name']} - {course.get('university', 'università')}\\n"
                    if course.get('snippet'):
                        prompt += f"   Info: {course['snippet']}\\n"
            
            # Aggiungi risultati ITS
            its_courses = search_results.get("its_courses", {}).get("courses", [])
            if its_courses:
                prompt += "\\n🔧 CORSI ITS TROVATI:\\n"
                for i, course in enumerate(its_courses[:2], 1):
                    prompt += f"{i}. {course['name'][:80]}...\\n"
                    if course.get('duration'):
                        prompt += f"   Durata: {course['duration']}\\n"
            
            prompt += """
BASANDOTI SUL PROFILO DELLO STUDENTE E SUI RISULTATI REALI TROVATI:
1. Fornisci un riepilogo PERSONALIZZATO di cosa hai capito del profilo
2. Suggerisci 2-3 percorsi CONCRETI (con nomi reali se disponibili)
3. Includi CONSIGLI PRATICI per i prossimi passi

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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=1000
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ Errore Gemini (raccomandazioni): {e}")
            return "Grazie per le informazioni! Ho analizzato il tuo profilo. Considera di consultare i siti ufficiali delle università per informazioni aggiornate sui corsi."
    
    def _build_profile_context'''

content = re.sub(method_pattern, new_method, content, flags=re.DOTALL)

with open('gemini_agent.py', 'w') as f:
    f.write(content)

print('✅ Agente aggiornato con ricerca web integrata')
