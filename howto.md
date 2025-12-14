# Først installer python3-venv, hvis det mangler

sudo apt install python3-venv

# Lav et nyt virtuelt miljø, f.eks. "venv"

python3 -m venv venv

# Aktivér venv

source venv/bin/activate

# Nu kan du installere yfinance uden fejl

pip install yfinance

# Lav et script, f.eks. start_venv.sh

````bash
# !/bin/bash

# Gå til din projektmappe
# C:\Users\mgn\OneDrive\nilfisk\src\python\stocks


# Aktivér venv

source venv/bin/activate

# (valgfrit) skriv en besked

echo "Venv aktiveret. Klar til at køre Python."
````

# Gør scriptet eksekverbart

 ````bash
 chmod +x start_venv.sh
 ````
