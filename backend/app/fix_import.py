with open('main.py', 'r') as f:
    content = f.read()

# Opzione 1: Import diretto se simple_agent.py è nella stessa cartella
new_content = content.replace(
    'from agent.simple_agent import SimpleCareerAgent',
    'from .agent.simple_agent import SimpleCareerAgent'
)

# Se non trova, prova alternativa
if 'from agent.simple_agent import SimpleCareerAgent' not in content:
    # Cerca la riga di import
    import re
    new_content = re.sub(
        r'from agent\.simple_agent import SimpleCareerAgent',
        '# Import corretto\nfrom .agent.simple_agent import SimpleCareerAgent',
        content
    )

with open('main.py', 'w') as f:
    f.write(new_content)

print("Import fix applicato")
