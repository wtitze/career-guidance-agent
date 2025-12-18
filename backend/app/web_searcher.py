"""
Modulo per la ricerca web di informazioni su corsi universitari, ITS e statistiche occupazionali.
"""
import requests
from typing import Dict, List, Any, Optional
import json
from duckduckgo_search import DDGS
import re
from urllib.parse import quote_plus


class WebSearcher:
    """Ricerca informazioni su corsi e opportunità formative sul web."""
    
    def __init__(self):
        self.university_domains = [
            'unibo.it', 'polimi.it', 'unipd.it', 'uniroma1.it', 
            'unimi.it', 'unito.it', 'unina.it', 'unifi.it',
            'units.it', 'unige.it', 'unipi.it', 'unict.it'
        ]
        
        self.its_keywords = ['ITS', 'Istituto Tecnico Superiore', 'tecnico superiore']
        
    def search_duckduckgo(self, query: str, max_results: int = 8) -> List[Dict[str, str]]:
        """Cerca su DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, region='it-it', max_results=max_results):
                    results.append({
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', '')[:200],
                        'source': 'duckduckgo'
                    })
                return results
        except Exception as e:
            print(f"⚠️  Errore ricerca DuckDuckGo: {e}")
            return []
    
    def search_university_courses(self, interests: List[str], location: str = None) -> Dict[str, Any]:
        """Cerca corsi universitari basati su interessi e località."""
        # Costruisci query
        query_terms = []
        
        if interests:
            query_terms.extend(interests[:2])  # Prendi i primi 2 interessi
        
        query = "corso di laurea " + " ".join(query_terms)
        
        if location:
            query += f" {location}"
        
        query += " università sito ufficiale"
        
        print(f"🔍 Ricerca corsi: {query}")
        
        # Cerca
        results = self.search_duckduckgo(query, max_results=10)
        
        # Filtra risultati universitari
        university_results = []
        for result in results:
            url = result.get('url', '').lower()
            if any(domain in url for domain in self.university_domains):
                university_results.append(result)
        
        # Estrai informazioni strutturate
        courses_info = self._extract_course_info(university_results, interests, location)
        
        return {
            'query': query,
            'total_results': len(results),
            'university_results': len(university_results),
            'courses': courses_info,
            'sources': university_results[:3]  # Top 3 fonti
        }
    
    def search_its_courses(self, interests: List[str], location: str = None) -> Dict[str, Any]:
        """Cerca corsi ITS."""
        query = "ITS corso"
        
        if interests:
            query += f" {' '.join(interests[:2])}"
        
        if location:
            query += f" {location}"
        
        query += " istituto tecnico superiore"
        
        print(f"🔍 Ricerca ITS: {query}")
        
        results = self.search_duckduckgo(query, max_results=8)
        
        # Filtra per ITS
        its_results = []
        for result in results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            if any(keyword in title or keyword in snippet for keyword in self.its_keywords):
                its_results.append(result)
        
        # Estrai informazioni ITS
        its_info = self._extract_its_info(its_results, interests, location)
        
        return {
            'query': query,
            'total_results': len(results),
            'its_results': len(its_results),
            'courses': its_info,
            'sources': its_results[:3]
        }
    
    def search_employment_stats(self, field: str, location: str = None) -> Dict[str, Any]:
        """Cerca statistiche occupazionali."""
        # Query per Almalaurea/Excelsior
        queries = [
            f"occupazione {field} Almalaurea",
            f"statistiche occupazionali {field}",
            f"sbocchi professionali {field}",
        ]
        
        if location:
            queries = [f"{q} {location}" for q in queries]
        
        all_results = []
        for query in queries[:2]:  # Solo prime 2 query
            results = self.search_duckduckgo(query, max_results=5)
            all_results.extend(results)
        
        # Filtra fonti attendibili
        reliable_sources = []
        for result in all_results:
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            
            # Fonti attendibili
            if any(source in url for source in ['almalaurea', 'excelsior', 'istat', 'miur', 'università']):
                reliable_sources.append(result)
            elif 'occupazion' in title or 'statistich' in title:
                reliable_sources.append(result)
        
        return {
            'field': field,
            'queries': queries[:2],
            'total_results': len(all_results),
            'reliable_sources': len(reliable_sources),
            'sources': reliable_sources[:3]
        }
    
    def _extract_course_info(self, results: List[Dict], interests: List[str], location: str = None) -> List[Dict]:
        """Estrae informazioni strutturate sui corsi."""
        courses = []
        
        for result in results[:5]:  # Analizza top 5
            title = result.get('title', '')
            url = result.get('url', '')
            snippet = result.get('snippet', '')
            
            # Estrai nome corso e università
            course_name = self._extract_course_name(title, snippet, interests)
            university = self._extract_university_name(title, url)
            
            if course_name:
                courses.append({
                    'name': course_name,
                    'university': university,
                    'url': url,
                    'snippet': snippet[:150] + '...',
                    'type': 'università',
                    'relevance': self._calculate_relevance(course_name, interests, location)
                })
        
        # Ordina per rilevanza
        courses.sort(key=lambda x: x['relevance'], reverse=True)
        
        return courses[:3]  # Top 3 corsi
    
    def _extract_its_info(self, results: List[Dict], interests: List[str], location: str = None) -> List[Dict]:
        """Estrae informazioni sui corsi ITS."""
        its_courses = []
        
        for result in results[:5]:
            title = result.get('title', '')
            url = result.get('url', '')
            snippet = result.get('snippet', '')
            
            # Cerca durata (es: "2 anni", "1800 ore")
            duration_match = re.search(r'(\d+)\s*(anni|ore|mesi)', snippet.lower())
            duration = duration_match.group(0) if duration_match else None
            
            course_info = {
                'name': title,
                'url': url,
                'snippet': snippet[:150] + '...',
                'type': 'ITS',
                'duration': duration,
                'relevance': self._calculate_relevance(title, interests, location)
            }
            
            its_courses.append(course_info)
        
        its_courses.sort(key=lambda x: x['relevance'], reverse=True)
        return its_courses[:3]
    
    def _extract_course_name(self, title: str, snippet: str, interests: List[str]) -> str:
        """Estrae il nome del corso dal titolo/snippet."""
        # Pattern comuni per nomi corsi
        patterns = [
            r'Corso di (.+?) -',
            r'Laurea in (.+?) -',
            r'(.+?) - Corso di laurea',
            r'(.+?) - Università'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1).strip()
        
        # Se non trovato, usa il titolo
        return title.split(' - ')[0] if ' - ' in title else title[:50]
    
    def _extract_university_name(self, title: str, url: str) -> str:
        """Estrae il nome dell'università."""
        # Cerca nel titolo
        for domain in self.university_domains:
            if domain in url:
                # Estrai nome dall'URL (es: "unibo.it" → "Alma Mater Bologna")
                domain_parts = domain.split('.')[0]
                if domain_parts == 'unibo':
                    return 'Alma Mater Studiorum - Bologna'
                elif domain_parts == 'polimi':
                    return 'Politecnico di Milano'
                elif domain_parts == 'unipd':
                    return 'Università di Padova'
                elif domain_parts == 'uniroma1':
                    return 'Sapienza Università di Roma'
                else:
                    return f"Università ({domain_parts})"
        
        # Cerca nel titolo
        if 'Politecnico' in title:
            return 'Politecnico'
        elif 'Università' in title:
            # Estrai testo dopo "Università"
            match = re.search(r'Universit[àa]\s+(.+)', title)
            if match:
                return f"Università {match.group(1).split(' - ')[0]}"
        
        return 'Università'
    
    def _calculate_relevance(self, text: str, interests: List[str], location: str = None) -> int:
        """Calcola rilevanza del risultato basata su interessi e località."""
        relevance = 0
        text_lower = text.lower()
        
        # Punteggio per interessi
        if interests:
            for interest in interests[:3]:
                if interest.lower() in text_lower:
                    relevance += 3
        
        # Punteggio per località
        if location and location.lower() in text_lower:
            relevance += 2
        
        # Bonus per "corso di laurea", "triennale", etc.
        keywords = ['corso', 'laurea', 'triennale', 'magistrale', 'master']
        for keyword in keywords:
            if keyword in text_lower:
                relevance += 1
        
        return relevance
    
    def search_for_student_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ricerca informazioni basate sul profilo studente."""
        print(f"🎯 Ricerca per profilo studente...")
        
        interests = profile_data.get('favorite_subjects', [])
        location = profile_data.get('location')
        school_type = profile_data.get('school_type', '')
        
        results = {
            'university_courses': [],
            'its_courses': [],
            'employment_stats': [],
            'recommendations': []
        }
        
        # 1. Cerca corsi universitari se interessi accademici
        if interests and len(interests) > 0:
            results['university_courses'] = self.search_university_courses(interests, location)
        
        # 2. Cerca ITS se profilo più tecnico/pratico
        if school_type and ('ITIS' in school_type or 'Tecnico' in school_type):
            results['its_courses'] = self.search_its_courses(interests, location)
        elif interests:
            # Prova comunque ITS se ci sono interessi tecnici
            technical_keywords = ['informatica', 'elettronica', 'meccanica', 'automazione']
            if any(keyword in ' '.join(interests).lower() for keyword in technical_keywords):
                results['its_courses'] = self.search_its_courses(interests, location)
        
        # 3. Cerca statistiche occupazionali per i primi 2 interessi
        if interests:
            for interest in interests[:2]:
                stats = self.search_employment_stats(interest, location)
                if stats['reliable_sources'] > 0:
                    results['employment_stats'].append(stats)
        
        # 4. Genera raccomandazioni basate sui risultati
        results['recommendations'] = self._generate_recommendations(results, profile_data)
        
        return results
    
    def _generate_recommendations(self, search_results: Dict, profile_data: Dict) -> List[str]:
        """Genera raccomandazioni basate sui risultati di ricerca."""
        recommendations = []
        
        # Raccomandazione università
        if search_results['university_courses'].get('courses'):
            courses = search_results['university_courses']['courses']
            if courses:
                best_course = courses[0]
                rec = f"📚 **{best_course['name']}** presso {best_course.get('university', 'università')}"
                if best_course.get('snippet'):
                    rec += f" - {best_course['snippet'][:100]}"
                recommendations.append(rec)
        
        # Raccomandazione ITS
        if search_results['its_courses'].get('courses'):
            its_courses = search_results['its_courses']['courses']
            if its_courses:
                best_its = its_courses[0]
                rec = f"🔧 **{best_its['name'][:50]}...** (ITS"
                if best_its.get('duration'):
                    rec += f", {best_its['duration']}"
                rec += ")"
                recommendations.append(rec)
        
        # Raccomandazione basata su statistiche
        if search_results['employment_stats']:
            stats = search_results['employment_stats'][0]
            if stats['reliable_sources'] > 0:
                recommendations.append(f"📊 Trovate {stats['reliable_sources']} fonti su opportunità occupazionali")
        
        # Raccomandazione generale
        if not recommendations:
            interests = profile_data.get('favorite_subjects', [])
            location = profile_data.get('location', '')
            
            if interests and location:
                recommendations.append(f"🔍 Considera corsi in {', '.join(interests[:2])} a {location}")
            elif interests:
                recommendations.append(f"🔍 Esplora corsi in {', '.join(interests[:2])}")
        
        return recommendations[:3]  # Massimo 3 raccomandazioni

