import re

with open('gemini_agent.py', 'r') as f:
    lines = f.readlines()

# Trova l'inizio e la fine del metodo
start_line = -1
end_line = -1
in_method = False
brace_count = 0

for i, line in enumerate(lines):
    if 'def _generate_recommendation_response' in line and start_line == -1:
        start_line = i
        in_method = True
    elif in_method:
        brace_count += line.count('    ')  # Conta indentazione
        if 'def ' in line and line.index('def ') == 0 and i > start_line and brace_count <= 4:
            end_line = i
            break

if start_line != -1 and end_line != -1:
    # Nuovo metodo con ricerca web
    new_method = '''    def _generate_recommendation_response(self, profile: StudentProfile, user_message: str) -> str:
        """Genera una risposta con raccomandazioni BASATE SU RICERCA WEB."""
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
        
        print(f"🔍 Avvio ricerca web per: {profile_data['favorite_subjects']} a {profile_data['location']}")
        
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
'''

    # Sostituisci il vecchio metodo
    lines[start_line:end_line] = [new_method + '\\n']
    
    with open('gemini_agent.py', 'w') as f:
        f.writelines(lines)
    
    print(f'✅ Metodo sostituito (righe {start_line+1}-{end_line+1})')
else:
    print('❌ Metodo non trovato')
