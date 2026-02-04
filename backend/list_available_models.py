#!/usr/bin/env python3
"""Script per listare i modelli Gemini disponibili con la propria API key."""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Configura API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Errore: GEMINI_API_KEY non trovata in .env")
    exit(1)

genai.configure(api_key=api_key)

try:
    print("📋 Elenco modelli disponibili:\n")
    
    # Elenca tutti i modelli
    models = genai.list_models()
    
    available_for_generation = []
    
    for model in models:
        # I modelli sono liste: [name, supported_methods]
        if isinstance(model, str):
            model_name = model.replace("models/", "")
        else:
            # Tenta di estrarre il nome
            try:
                model_name = str(model).replace("models/", "")
            except:
                continue
        
        available_for_generation.append(model_name)
        print(f"✅ {model_name}")
    
    if available_for_generation:
        print("\n✨ Modelli disponibili (usa uno di questi nel .env):")
        for model in available_for_generation:
            print(f"  GEMINI_MODEL={model}")
    else:
        print("\n⚠️  Nessun modello trovato!")
        
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()
