# Projekt: stock_work

Dette repository indeholder et Python-program til arbejde med aktiedata.

## Forudsætninger

- Python 3.10+ anbefales
- `pip` (brug `python -m pip` hvis `pip` ikke findes)

## Opret og aktivér et virtuelt miljø (venv)

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Windows (CMD):

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

macOS / Linux / WSL:

```bash
python3 -m venv venv
source venv/bin/activate
```

Hvis du får en fejl ved aktivering i PowerShell, kan det skyldes execution policy. Kør eventuelt (som administrator) `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` eller brug CMD/WSL i stedet.

## Installer afhængigheder

Når venv er aktiveret, installer dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Hvis `requirements.txt` ikke findes eller er ufuldstændig, kan du generere en ny fil efter at have installeret pakker:

```bash
pip freeze > requirements.txt
```

## Kør programmet

Fra projektroden (sørg for at venv er aktiveret):

```bash
python app.py
```

På systemer med Bash (WSL, macOS, Linux) kan du også køre `start.sh`:

```bash
bash start.sh
```

## Stop / deaktiver venv

```bash
deactivate
```

## Fejlretningstips

- Hvis `pip` ikke findes: brug `python -m pip install -r requirements.txt`.
- Hvis Python-version er forkert: installer en understøttet Python-version og gentag venv-opsætningen.
- Hvis du mangler datafiler som `tickers.json` eller `stock_scores.csv`, tjek at du er i projektroden.


## add in github

````bash
git init
git add .
git commit -m "Initial commit"
````

## .gitignore

For at undgå at uønskede filer bliver inkluderet i versionkontrol, skal du sørge for at have en `.gitignore` fil med følgende indhold:

```
venv/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
*.log
*.sqlite3
.env
.DS_Store
```
