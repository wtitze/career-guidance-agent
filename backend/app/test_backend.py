#!/usr/bin/env python3
"""
Script di test per verificare che il backend funzioni
"""
import sys
import os

# Percorso assoluto alla directory data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')

def test_imports():
    """Testa che tutte le importazioni funzionino"""
    try:
        from main import app
        print("✅ Import di FastAPI riuscito")
        
        # Verifica che l'app abbia gli endpoint corretti
        routes = [(route.path, route.methods) for route in app.routes]
        print(f"✅ Trovati {len(routes)} endpoint:")
        for path, methods in routes:
            print(f"   - {path} {methods}")
        
        return True
    except Exception as e:
        print(f"❌ Errore nelle importazioni: {e}")
        return False

def test_environment():
    """Testa che le variabili d'ambiente siano configurate"""
    required_dirs = [
        os.path.join(DATA_DIR, 'cache'),
        os.path.join(DATA_DIR, 'sqlite'), 
        os.path.join(DATA_DIR, 'fallback')
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory {os.path.basename(dir_path)} esiste")
        else:
            print(f"❌ Directory {os.path.basename(dir_path)} mancante")
            all_exist = False
    
    return all_exist

def test_dependencies():
    """Testa che le dipendenze principali siano importabili"""
    dependencies = [
        ('numpy', 'np'),
        ('pandas', 'pd'),
        ('spacy', 'spacy'),
        ('fastapi', 'fastapi'),
        ('sqlalchemy', 'sa')
    ]
    
    all_ok = True
    for module, alias in dependencies:
        try:
            __import__(module)
            print(f"✅ {module} importato")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            all_ok = False
    
    return all_ok

def test_spacy_model():
    """Testa che il modello spaCy italiano funzioni"""
    try:
        import spacy
        nlp = spacy.load("it_core_news_sm")
        doc = nlp("Il backend funziona correttamente.")
        print(f"✅ Modello spaCy italiano: OK ({len(doc)} tokens)")
        return True
    except Exception as e:
        print(f"⚠️  Modello spaCy: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test del backend...")
    print("-" * 40)
    
    success = True
    
    # Esegui i test
    if not test_environment():
        success = False
    
    if not test_imports():
        success = False
        
    if not test_dependencies():
        success = False
        
    if not test_spacy_model():
        print("⚠️  Modello spaCy non critico, si può procedere")
    
    print("-" * 40)
    if success:
        print("🎉 Tutti i test passati! Il backend è configurato correttamente.")
        print("💡 Per avviare il server: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("⚠️  Alcuni test falliti. Controlla la configurazione.")
        sys.exit(1)
