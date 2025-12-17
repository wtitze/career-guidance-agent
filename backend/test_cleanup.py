import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
import re

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')

client = genai.Client(api_key=api_key)

prompt = '''Analizza: "Abito a Milano"
Rispondi SOLO con questo JSON: [{"field_name": "location", "value": "Milano", "confidence": "alta"}]
Se non trovi info: []'''

print('🧪 Test pulizia JSON...')

try:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=200
        )
    )
    
    text = response.text.strip()
    print(f'1. Originale: "{text}"')
    
    # Metodo 1: semplice replace
    text1 = text.replace('```json', '').replace('```', '').strip()
    print(f'2. Replace semplice: "{text1}"')
    
    # Metodo 2: regex per estrarre solo il JSON
    json_pattern = r'(\[.*\]|\{.*\})'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        text2 = match.group(1).strip()
        print(f'3. Regex extract: "{text2}"')
        text = text2
    else:
        text = text1
    
    print(f'4. Finale per parsing: "{text}"')
    
    if text and text not in ['[]', '{}']:
        data = json.loads(text)
        print(f'✅ JSON parsato: {data}')
    else:
        print('ℹ️  Nessuna info')
        
except Exception as e:
    print(f'❌ Errore: {e}')
