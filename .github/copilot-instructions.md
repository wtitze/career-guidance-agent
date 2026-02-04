# Istruzioni per Agenti di Programmazione AI per Career Guidance Agent

## Panoramica Architetturale
Questo è un sistema full-stack basato su AI per l'orientamento post-diploma degli studenti italiani:
- **Frontend**: Interfaccia chat Next.js 16 + TypeScript + Tailwind CSS (`frontend/`)
- **Backend**: API FastAPI Python con agente AI Gemini (`backend/app/`)
- **Dati**: Persistenza SQLite, caching sessioni Redis opzionale (`data/`)

L'architettura segue i principi di modularità e scalabilità del Capitolo 6 di "AI Engineering" di Chip Huyen, con componenti separati per agente AI, ricerca web, gestione stato e interfaccia utente.

## Componenti Core
- `GeminiOrientationAgent` (`backend/app/gemini_agent.py`): Logica AI principale usando Google Gemini 2.5-flash-lite
- `StudentProfile` (`backend/app/student_profile.py`): Modello Pydantic per tracciare interessi, obiettivi, vincoli dello studente
- `StateManager` (`backend/app/state_manager.py`): Gestione sessioni (Redis con fallback in memoria)
- `WebSearcher` (`backend/app/web_searcher.py`): Integrazione DuckDuckGo per info real-time su corsi/lavoro
- `ChatInterface` (`frontend/components/ChatInterface/`): Componente React per conversazioni utente

## Flusso Dati
1. Utente invia messaggio via chat frontend
2. Frontend posta a `/api/chat` con `{message, session_id}`
3. Backend recupera/aggiorna `StudentProfile` da `StateManager`
4. `GeminiOrientationAgent` elabora messaggio, estrae info, aggiorna profilo in modo conversazionale (senza interrogatorio diretto)
5. Agente chiama `WebSearcher` per dati italiani su università/ITS/lavoro, considerando location e budget
6. Risposta restituita con `conversation_history` aggiornata e `recommendations` specifiche (es. link a università, siti ditte)

## Pattern Chiave
- **Architettura Fallback**: Agente Gemini ricade su `SimpleCareerAgent` se API non disponibile
- **Risposte Guidate dal Profilo**: Aggiorna sempre campi `StudentProfile` (interessi, location, obiettivi) dalla conversazione
- **Contesto Italiano**: Tutto in italiano; focus su università, ITS, sistemi lavoro italiani
- **Persistenza Sessioni**: Usa `session_id` per continuità; profili memorizzati via `StateManager`
- **Integrazione Web**: Cerca "corso di laurea [interessi]" o "ITS [campo]" per raccomandazioni, fornendo link e info base
- **Raccolta Conversazionale**: Raccogli info (personalità, carattere, interessi) naturalmente, senza interrogatorio
- **Considerazioni Locali**: Tieni conto della città dello studente e budget per proposte (es. evitare spostamenti costosi)

## Workflow Sviluppo
- **Backend**: `cd backend && uvicorn app.main:app --reload` (richiede `GEMINI_API_KEY` in `.env`)
- **Frontend**: `cd frontend && npm run dev` (chiamate API hardcoded a URL GitHub dev in `services/api.ts`)
- **Ambiente**: Imposta `GEMINI_API_KEY`, opzionale `REDIS_HOST/PORT`, `AGENT_TEMPERATURE=0.7`
- **Testing**: Esegui `python -m pytest` in backend; frontend usa build Next.js standard

## Convenzioni Codice
- **Import**: Usa import assoluti in backend (`from student_profile import ...`)
- **Gestione Errori**: Fallback graziosi (es. controlli disponibilità agente in `main.py`)
- **Logging**: Usa modulo `logging` con messaggi italiani per errori user-facing
- **Modelli API**: Pydantic `BaseModel` per richieste/risposte; mantieni compatibilità backward
- **Frontend**: Stato client-side per `messages[]`, `sessionId`; auto-scroll all'ultimo messaggio

## Task Comuni
- **Aggiungere Campi Profilo**: Aggiorna modello `StudentProfile` e logica estrazione agente
- **Nuove Raccomandazioni**: Estendi `WebSearcher` con scraping siti educativi italiani
- **Miglioramenti UI**: Modifica componenti `ChatInterface`; usa Radix UI per consistenza
- **Estensioni API**: Aggiungi endpoint in `main.py` seguendo pattern FastAPI

## Dipendenze
- Backend: `google-genai`, `duckduckgo-search`, `fastapi`, `pydantic`, `redis` (opzionale)
- Frontend: `axios` per chiamate API, `lucide-react` per icone, `@radix-ui/*` per componenti