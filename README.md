# Projekt: stock_work

Dette repository indeholder et Python-program til arbejde med aktiedata.

## Forudsætninger

- Python 3.10+ anbefales
- `pip` (brug `python -m pip` hvis `pip` ikke findes)

## Python 3 – uv setup fra scratch

Denne guide viser, hvordan du starter et Python-projekt helt fra bunden med **uv** som virtual environment og dependency manager.

---

## 1️⃣ Start med tom projektmappe

```bash
mkdir my_project
cd my_project
touch main.py

# Installer uv (kun én gang på maskinen)
curl -LsSf https://astral.sh/uv/install.sh | sh

# check version
uv --version

# Initialisér projekt med uv
uv init
````

## Dette opretter

- pyproject.toml → projektmetadata og dependencies
- .python-version → Python-version uv skal bruge

## Opret virtual environment

````bash
uv venv
````

## run program

````bash
python main.py
````

## add in github

````bash
git init
git add .
git commit -m "Initial commit"

# setup github
git remote add origin https://github.com/MichaelGNielsen/StocksDash.git

# push to github
git remote -v
git push
git push --set-upstream origin master

# omdøb til main
git branch -m master main

# push til main
git push -u origin main
````


## add in github

````bash
git init
git add .
git commit -m "Initial commit"
````

## .gitignore

For at undgå at uønskede filer bliver inkluderet i versionkontrol, skal du sørge for at have en `.gitignore` fil med følgende indhold:

````bash
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
````
