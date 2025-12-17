"""
Test semplice per verificare il funzionamento del profilo studente.
"""
# Import assoluti
try:
    from student_profile import StudentProfile
    from state_manager import state_manager
except ImportError:
    # Fallback se eseguito come script principale
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from student_profile import StudentProfile
    from state_manager import state_manager

def test_profile_creation():
    """Test creazione profilo base."""
    print("🧪 Test 1: Creazione profilo studente...")
    
    profile = StudentProfile()
    profile.update_field("location", "Bologna")
    profile.update_field("school_type", "ITIS Informatica")
    profile.favorite_subjects = ["Matematica", "Informatica"]  # Assegnazione diretta per lista
    profile.update_field("primary_goal", "occupazione")
    profile.update_field("institution_preference", "pubblico")
    
    print(f"✅ Profilo creato: {profile.session_id}")
    print(f"📍 Località: {profile.location}")
    print(f"📚 Materie preferite: {profile.favorite_subjects}")
    print(f"🎯 Completamento: {profile.profile_completeness*100:.1f}%")
    print(f"🔍 Pronto per ricerca? {profile.is_sufficient_for_search()}")
    
    return profile

def test_state_manager():
    """Test del gestore di stato."""
    print("\n🧪 Test 2: Gestore di stato...")
    
    # Crea una nuova sessione
    profile = state_manager.create_session()
    session_id = profile.session_id
    
    print(f"✅ Sessione creata: {session_id}")
    
    # Modifica profilo
    profile.update_field("location", "Milano")
    profile.hobbies = ["calcio", "programmazione"]  # Assegnazione diretta
    
    # Salva nel gestore
    state_manager.update_session(session_id, profile)
    
    # Recupera profilo
    retrieved = state_manager.get_session(session_id)
    
    if retrieved and retrieved.location == "Milano":
        print("✅ Profilo recuperato correttamente")
        print(f"📍 Località recuperata: {retrieved.location}")
        print(f"⚽ Hobby: {retrieved.hobbies}")
    else:
        print("❌ Errore nel recupero del profilo")
    
    return retrieved

def test_conversation_history():
    """Test della cronologia conversazione."""
    print("\n🧪 Test 3: Cronologia conversazione...")
    
    profile = StudentProfile()
    
    # Simula conversazione
    profile.add_conversation_turn("user", "Mi piace la matematica")
    profile.add_conversation_turn("agent", "Dove vivi?")
    profile.add_conversation_turn("user", "A Bologna")
    profile.add_conversation_turn("agent", "Che diploma hai?")
    
    print(f"✅ Turni conversazione: {len(profile.conversation_history)}")
    for i, turn in enumerate(profile.conversation_history, 1):
        print(f"  {i}. {turn['role']}: {turn['message'][:50]}...")
    
    return profile

def test_missing_info_priority():
    """Test della lista di informazioni mancanti."""
    print("\n🧪 Test 4: Priorità informazioni mancanti...")
    
    profile = StudentProfile()
    profile.update_field("location", "Roma")
    # Altri campi lasciati vuoti
    
    print("ℹ️  Profilo parziale creato")
    print(f"📍 Località: {profile.location}")
    print(f"📋 Info mancanti (priorità): {profile.missing_info_priority}")
    
    # Mostra riepilogo
    print("\n" + profile.get_summary())
    
    return profile

if __name__ == "__main__":
    print("🚀 Avvio test modulo profilo studente...")
    print("=" * 50)
    
    test1_profile = test_profile_creation()
    test2_profile = test_state_manager()
    test3_profile = test_conversation_history()
    test4_profile = test_missing_info_priority()
    
    print("\n" + "=" * 50)
    print("✅ Tutti i test completati!")
    print(f"📊 Profilo finale pronto per ricerca: {test1_profile.is_sufficient_for_search()}")
