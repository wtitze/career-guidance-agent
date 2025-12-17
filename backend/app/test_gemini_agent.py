"""
Test per l'agente Gemini.
"""
import sys
import os

# Aggiungi la directory corrente al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gemini_agent import orientation_agent, GeminiOrientationAgent
    from state_manager import state_manager
    from student_profile import StudentProfile  # Aggiunto questo import
except ImportError as e:
    print(f"❌ Errore import: {e}")
    import traceback
    traceback.print_exc()
    print("\nVerifica che tutti i file esistano:")
    print("  - gemini_agent.py")
    print("  - state_manager.py") 
    print("  - student_profile.py")
    sys.exit(1)

def test_agent_initialization():
    """Test inizializzazione agente."""
    print("🧪 Test 1: Inizializzazione agente Gemini...")
    
    if orientation_agent is None:
        print("⚠️  Agente non inizializzato")
        return None
    else:
        print("✅ Agente inizializzato correttamente")
        return orientation_agent

def test_new_conversation(agent):
    """Test avvio nuova conversazione."""
    print("\n🧪 Test 2: Avvio nuova conversazione...")
    
    if agent is None:
        print("⚠️  Simulazione (agente non disponibile)")
        profile = state_manager.create_session()
        welcome = "Ciao! Sono il tuo orientatore virtuale. Dove vivi attualmente?"
        profile.add_conversation_turn("agent", welcome)
        state_manager.update_session(profile.session_id, profile)
        
        print(f"✅ Sessione creata: {profile.session_id[:8]}...")
        return profile
    else:
        try:
            welcome, profile = agent.start_new_conversation()
            print(f"✅ Sessione creata: {profile.session_id[:8]}...")
            return profile
        except Exception as e:
            print(f"❌ Errore start_new_conversation: {e}")
            return None

def test_conversation_flow(agent, profile):
    """Test flusso conversazionale."""
    print("\n🧪 Test 3: Flusso conversazionale...")
    
    if profile is None:
        print("❌ Nessun profilo disponibile")
        return None
    
    test_messages = [
        "Abito a Milano",
        "Frequento il liceo scientifico",
        "Mi piacciono matematica e fisica",
        "Vorrei trovare un lavoro dopo gli studi",
    ]
    
    session_id = profile.session_id
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Messaggio {i}/4 ---")
        print(f"👤 Studente: {message}")
        
        if agent is None:
            # Simula risposta
            profile.add_conversation_turn("user", message)
            
            if not profile.location:
                response = "Perfetto, Milano! Sei disposto a spostarti?"
                profile.location = "Milano"
            elif not profile.school_type:
                response = "Liceo scientifico, ottima base!"
                profile.school_type = "Liceo Scientifico"
            elif not profile.favorite_subjects:
                response = "Matematica e fisica sono fondamentali!"
                profile.favorite_subjects = ["Matematica", "Fisica"]
            else:
                response = "Capisco che punti all'inserimento lavorativo."
                profile.primary_goal = "occupazione"
            
            print(f"🤖 Agente: {response}")
            profile.add_conversation_turn("agent", response)
        else:
            # Usa l'agente reale
            try:
                response, updated_profile = agent.process_message(session_id, message)
                profile = updated_profile
                print(f"🤖 Agente: {response[:100]}...")
            except Exception as e:
                print(f"❌ Errore process_message: {e}")
                break
        
        print(f"📊 Completamento: {profile.profile_completeness*100:.1f}%")
    
    print(f"\n🎯 PROFILO FINALE:")
    print(profile.get_summary())
    
    return profile

def test_multiple_sessions():
    """Test gestione multiple sessioni."""
    print("\n🧪 Test 4: Sessioni multiple...")
    
    profile1 = state_manager.create_session()
    profile1.update_field("location", "Roma")
    profile1.update_field("school_type", "ITIS Informatica")
    
    profile2 = state_manager.create_session()
    profile2.update_field("location", "Torino")
    profile2.update_field("school_type", "Liceo Classico")
    
    retrieved1 = state_manager.get_session(profile1.session_id)
    retrieved2 = state_manager.get_session(profile2.session_id)
    
    if retrieved1 and retrieved2:
        print("✅ Gestione sessioni multiple funzionante")
    else:
        print("❌ Errore nel recupero sessioni")

def main():
    """Funzione principale di test."""
    print("🚀 TEST AGENTE GEMINI")
    print("=" * 40)
    
    agent = test_agent_initialization()
    profile = test_new_conversation(agent)
    
    if profile:
        profile = test_conversation_flow(agent, profile)
        test_multiple_sessions()
    
    print("\n" + "=" * 40)
    print("✅ TEST COMPLETATI")

if __name__ == "__main__":
    main()
