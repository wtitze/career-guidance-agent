"""
Modulo per la gestione del profilo studente.
Rappresenta lo stato interno dell'agente.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class StudentProfile(BaseModel):
    """Profilo strutturato dello studente per l'orientamento universitario."""
    
    # === ID e Metadati ===
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # === A. Informazioni Demografiche/Contestuali ===
    location: Optional[str] = None  # Città/Regione
    willing_to_relocate: Optional[bool] = None
    relocation_radius: Optional[str] = None  # "Nessuno", "Regionale", "Nazionale", "Internazionale"
    school_type: Optional[str] = None  # Tipo di diploma
    diploma_score: Optional[float] = None  # Voto diploma
    regular_path: Optional[bool] = None  # Percorso scolastico regolare
    current_status: Optional[str] = None  # "5° anno", "Diplomato", "Lavoratore"
    has_job: Optional[bool] = None  # Lavora attualmente?
    
    # === B. Interessi e Attitudini ===
    favorite_subjects: List[str] = Field(default_factory=list)
    disliked_subjects: List[str] = Field(default_factory=list)
    learning_style: Optional[str] = None  # "teorico", "pratico", "misto"
    soft_skills: List[str] = Field(default_factory=list)  # ["teamwork", "leadership", ...]
    hobbies: List[str] = Field(default_factory=list)
    relevant_experiences: List[str] = Field(default_factory=list)
    
    # === C. Obiettivi e Vincoli ===
    primary_goal: Optional[str] = None  # "occupazione", "stipendio", "passione", "prestigio"
    further_studies: Optional[bool] = None  # Intende fare Master/Dottorato?
    preferred_course_length: Optional[str] = None  # "breve", "triennale", "lungo"
    institution_preference: Optional[str] = None  # "pubblico", "privato", "indifferente"
    budget_constraint: Optional[str] = None  # "basso", "medio", "alto"
    time_constraint: Optional[str] = None  # "tempo pieno", "part-time", "serale"
    health_constraints: List[str] = Field(default_factory=list)
    
    # === D. Stato della Conversazione ===
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    profile_completeness: float = 0.0  # 0.0 a 1.0
    missing_info_priority: List[str] = Field(default_factory=list)
    
    def update_field(self, field: str, value: Any) -> None:
        """Aggiorna un campo e marca come modificato."""
        setattr(self, field, value)
        self.last_updated = datetime.now()
        self._update_completeness()
    
    def add_conversation_turn(self, role: str, message: str) -> None:
        """Aggiunge un turno alla cronologia della conversazione."""
        self.conversation_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _update_completeness(self) -> None:
        """Calcola quanto è completo il profilo (semplificato)."""
        critical_fields = [
            'location', 'school_type', 'favorite_subjects', 
            'primary_goal', 'institution_preference'
        ]
        
        completed = 0
        for field in critical_fields:
            value = getattr(self, field)
            # Controlla se il campo ha un valore valido
            if value not in [None, [], ""]:
                if isinstance(value, list):
                    if len(value) > 0:  # Lista non vuota
                        completed += 1
                else:
                    completed += 1
        
        self.profile_completeness = completed / len(critical_fields) if critical_fields else 0.0
        self._update_missing_info()
    
    def _update_missing_info(self) -> None:
        """Aggiorna la lista delle informazioni mancanti in ordine di priorità."""
        self.missing_info_priority = []
        
        # Priority 1: Informazioni critiche
        if not self.location:
            self.missing_info_priority.append("location")
        if not self.school_type:
            self.missing_info_priority.append("school_type")
        if not self.favorite_subjects:
            self.missing_info_priority.append("favorite_subjects")
        
        # Priority 2: Informazioni importanti
        if not self.primary_goal:
            self.missing_info_priority.append("primary_goal")
        if not self.institution_preference:
            self.missing_info_priority.append("institution_preference")
        if self.willing_to_relocate is None:
            self.missing_info_priority.append("willing_to_relocate")
        
        # Priority 3: Informazioni di approfondimento
        if not self.hobbies:
            self.missing_info_priority.append("hobbies")
        if not self.learning_style:
            self.missing_info_priority.append("learning_style")
    
    def is_sufficient_for_search(self) -> bool:
        """Determina se il profilo è abbastanza completo per iniziare la ricerca."""
        return self.profile_completeness >= 0.6  # Almeno 60% delle info critiche
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il profilo in dizionario per serializzazione."""
        # In Pydantic v2 usiamo model_dump() invece di dict()
        return self.model_dump()
    
    def get_summary(self) -> str:
        """Restituisce un riepilogo testuale del profilo."""
        summary = [
            "=== RIEPILOGO PROFILO STUDENTE ===",
            f"Sessione: {self.session_id[:8]}...",
            f"Completamento: {self.profile_completeness*100:.1f}%",
            "",
            "INFORMAZIONI PRINCIPALI:",
            f"- Località: {self.location or 'Non specificata'}",
            f"- Tipo scuola: {self.school_type or 'Non specificato'}",
            f"- Materie preferite: {', '.join(self.favorite_subjects) or 'Nessuna'}",
            f"- Obiettivo primario: {self.primary_goal or 'Non specificato'}",
            f"- Preferenza istituzione: {self.institution_preference or 'Non specificata'}",
        ]
        
        if self.hobbies:
            summary.append(f"- Hobby: {', '.join(self.hobbies)}")
        if self.willing_to_relocate is not None:
            summary.append(f"- Disponibile a trasferirsi: {'Sì' if self.willing_to_relocate else 'No'}")
        
        return "\n".join(summary)
