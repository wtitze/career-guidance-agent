with open('main.py', 'r') as f:
    content = f.read()

# Nuova configurazione CORS
new_cors = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://fluffy-waddle-5g99rp4w79346xq-3000.app.github.dev",
        "https://fluffy-waddle-5g99rp4w79346xq-8000.app.github.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

# Trova e sostituisci tutta la sezione CORS
import re
pattern = r'app\.add_middleware\(\s*CORSMiddleware,[^)]+\)'
new_content = re.sub(pattern, new_cors, content, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(new_content)

print("✅ CORS aggiornato con successo!")
