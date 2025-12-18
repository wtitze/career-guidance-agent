"""
Modulo per la ricerca web - versione corretta.
"""
import requests
from typing import Dict, List, Any, Optional
import json
from duckduckgo_search import DDGS
import re


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
        if not interests:
            return {'courses': [], 'query': '', 'total_results': 0}
        
        query_terms = interests[:2]
        query = "corso di laurea " + " ".join(query_terms)
        
        if location:
            query += f" {location}"
        
        query += " università sito ufficiale"
        
        print(f"🔍 Ricerca corsi: {query}")
        
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
            'sources': university_results[:3]
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
    
    def search_for_student_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ricerca informazioni basate sul profilo studente."""
        print(f"🎯 Ricerca per profilo studente...")
        
        interests = profile_data.get('favorite_subjects', [])
        location = profile_data.get('location')
        school_type = profile_data.get('school_type', '')
        
        results = {
            'university_courses': self.search_university_courses(interests, location),
            'its_courses': self.search_its_courses(interests, location),
            'recommendations': []
        }
        
        # Genera raccomandazioni
        results['recommendations'] = self._generate_recommendations(results, profile_data)
        
        return results
    
    def _extract_course_info(self, results: List[Dict], interests: List[str], location: str = None) -> List[Dict]:
        """Estrae informazioni strutturate sui corsi."""
        courses = []
        
        for result in results[:5]:
            title = result.get('title', '')
            url = result.get('url', '')
            snippet = result.get('snippet', '')
            
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
        
        courses.sort(key=lambda x: x['relevance'], reverse=True)
        return courses[:3]
    
    def _extract_its_info(self, results: List[Dict], interests: List[str], location: str = None) -> List[Dict]:
        """Estrae informazioni sui corsi ITS."""
        its_courses = []
        
        for result in results[:5]:
            title = result.get('title', '')
            url = result.get('url', '')
            snippet = result.get('snippet', '')
            
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
        
        return title.split(' - ')[0] if ' - ' in title else title[:50]
    
    def _extract_university_name(self, title: str, url: str) -> str:
        """Estrae il nome dell'università."""
        for domain in self.university_domains:
            if domain in url:
                domain_parts = domain.split('.')[0]
                if domain_parts == 'unibo':
                    return 'Alma Mater Bologna'
                elif domain_parts == 'polimi':
                    return 'Politecnico di Milano'
                elif domain_parts == 'unipd':
                    return 'Università di Padova'
                elif domain_parts == 'uniroma1':
                    return 'Sapienza Roma'
                else:
                    return f"Università ({domain_parts})"
        
        if 'Politecnico' in title:
            return 'Politecnico'
        elif 'Università' in title:
            match = re.search(r'Universit[àa]\s+(.+)', title)
            if match:
                return f"Università {match.group(1).split(' - ')[0]}"
        
        return 'Università'
    
    def _calculate_relevance(self, text: str, interests: List[str], location: str = None) -> int:
        """Calcola rilevanza del risultato."""
        relevance = 0
        text_lower = text.lower()
        
        if interests:
            for interest in interests[:3]:
                if interest.lower() in text_lower:
                    relevance += 3
        
        if location and location.lower() in text_lower:
            relevance += 2
        
        keywords = ['corso', 'laurea', 'triennale', 'magistrale']
        for keyword in keywords:
            if keyword in text_lower:
                relevance += 1
        
        return relevance
    
    def _generate_recommendations(self, search_results: Dict, profile_data: Dict) -> List[str]:
        """Genera raccomandazioni basate sui risultati di ricerca."""
        recommendations = []
        
        # Raccomandazione università
        uni_courses = search_results.get('university_courses', {}).get('courses', [])
        if uni_courses:
            best_course = uni_courses[0]
            rec = f"🎓 **{best_course['name']}** presso {best_course.get('university', 'università')}"
            recommendations.append(rec)
        
        # Raccomandazione ITS
        its_courses = search_results.get('its_courses', {}).get('courses', [])
        if its_courses:
            best_its = its_courses[0]
            rec = f"🔧 **ITS**: {best_its['name'][:60]}..."
            if best_its.get('duration'):
                rec += f" ({best_its['duration']})"
            recommendations.append(rec)
        
        # Raccomandazione generale se nessun corso trovato
        if not recommendations:
            interests = profile_data.get('favorite_subjects', [])
            location = profile_data.get('location', '')
            
            if interests and location:
                recommendations.append(f"🔍 Esplora corsi in {', '.join(interests[:2])} a {location}")
            elif interests:
                recommendations.append(f"🔍 Considera formazione in {', '.join(interests[:2])}")
            else:
                recommendations.append("🔍 Consulta i siti ufficiali delle università per informazioni aggiornate")
        
        return recommendations[:3]

