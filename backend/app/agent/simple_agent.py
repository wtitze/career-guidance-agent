"""
Agente AI semplice per l'orientamento (versione temporanea)
"""
import random
from typing import Dict, Any, List

class SimpleCareerAgent:
    """Agente semplice che risponde a domande di orientamento"""
    
    def __init__(self):
        self.greetings = [
            "Ciao! Sono qui per aiutarti con l'orientamento post-diploma.",
            "Benvenuto! Sono il tuo assistente per scelte universitarie e professionali.",
            "Salve! Posso aiutarti a scoprire percorsi dopo il diploma."
        ]
        
        self.university_responses = {
            "informatica": [
                "Per Informatica ti consiglio: Università di Bologna, Politecnico di Milano, Sapienza di Roma.",
                "I migliori corsi di Informatica in Italia sono al Politecnico di Milano e di Torino.",
                "Informatica: triennale + magistrale, alta occupazione (85% dopo 1 anno)."
            ],
            "medicina": [
                "Medicina: 6 anni, test d'ingresso nazionale, specializzazione dopo la laurea.",
                "Per Medicina preparati al test d'ingresso. Le migliori sono Statale di Milano, Bologna, Padova."
            ],
            "ingegneria": [
                "Ingegneria: Politecnico di Milano e Torino eccellono. Specializzazioni: civile, gestionale, biomedica.",
                "Ingegneria ha molte specializzazioni. Le migliori università sono i Politecnici."
            ]
        }
        
        self.its_responses = [
            "Gli ITS (Istituti Tecnici Superiori) sono corsi di 2 anni con stage in azienda. Tasso occupazione 90%.",
            "ITS: formazione tecnica superiore, durata 2 anni, alta occupazione. Settori: digitale, meccatronica, turismo.",
            "ITS sono alternativi all'università: più pratici, durano meno, ottimi per entrare subito nel lavoro."
        ]
        
        self.default_responses = [
            "Posso aiutarti con informazioni su università, ITS, o mondo del lavoro. Cosa ti interessa di più?",
            "Mi concentro su orientamento post-diploma: università, corsi ITS, opportunità lavorative.",
            "Per darti una risposta migliore, dimmi i tuoi interessi o cosa vorresti fare dopo il diploma."
        ]
    
    def process_message(self, user_message: str) -> str:
        """Processa il messaggio dell'utente e restituisce una risposta"""
        message_lower = user_message.lower()
        
        # Saluti
        if any(word in message_lower for word in ["ciao", "buongiorno", "salve", "hello"]):
            return random.choice(self.greetings)
        
        # Università
        if any(word in message_lower for word in ["università", "universita", "laurea", "corso di laurea"]):
            if "informatica" in message_lower:
                return random.choice(self.university_responses["informatica"])
            elif "medicina" in message_lower:
                return random.choice(self.university_responses["medicina"])
            elif "ingegneria" in message_lower:
                return random.choice(self.university_responses["ingegneria"])
            else:
                return "Di quale facoltà universitaria vorresti informazioni? (es: Informatica, Medicina, Ingegneria)"
        
        # ITS
        if any(word in message_lower for word in ["its", "istituto tecnico superiore", "tecnico superiore"]):
            return random.choice(self.its_responses)
        
        # Lavoro
        if any(word in message_lower for word in ["lavoro", "occupazione", "carriera", "professione"]):
            return "Dopo il diploma puoi: 1) Cercare lavoro diretto, 2) Fare un ITS (2 anni), 3) Andare all'università. Cosa preferisci?"
        
        # Domande specifiche
        if "milano" in message_lower:
            return "A Milano ci sono: Politecnico (ingegneria/architettura), Statale (tutte le facoltà), Bicocca (scienze/economia)."
        
        if "bologna" in message_lower:
            return "Bologna ha una delle università più antiche al mondo. Ottima per Giurisprudenza, Medicina, Lettere."
        
        # Risposta default
        return random.choice(self.default_responses)
