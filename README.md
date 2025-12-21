# Projekt: stock_work

Dette repository indeholder et Python-program til arbejde med aktiedata.

Projektet kører i **WSL2 (Ubuntu 24)** med **uv** som dependency manager.

---

## Første gang: Initialisering af projektet med uv

Kør disse kommandoer første gang du sætter projektet op:

### 1. Installer uv (hvis ikke allerede installeret)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

### 2. Opret virtual environment

```bash
cd ~/path/to/stocks  # naviger til projektmappen
uv venv
```

Denne kommando opretter en `.venv` mappe med Python-miljøet.

### 3. Installer dependencies

```bash
uv sync
```

Dette installerer alle pakker defineret i `pyproject.toml` baseret på `uv.lock`.

### 4. Aktivér virtual environment

```bash
source .venv/bin/activate
```

Efter aktivering vil kommandolinjen vise `(.venv)` i starten.

---

## Efter PC-genstart

Hver gang du genstarter din PC og åbner WSL2 igen, skal du blot:

### 1. Naviger til projektmappen

```bash
cd ~/path/to/stocks
```

### 2. Aktivér virtual environment

```bash
source .venv/bin/activate
```

### 3. Kør programmet

```bash
# Metode 1: Med aktiveret virtual environment
python main.py

# Metode 2: Direkte med uv (uden at aktivere venv)
uv run python main.py
```

**Det er det!** Du behøver ikke køre `uv venv` eller `uv sync` igen – alt er allerede sat op.

---

## Almindelige kommandoer

```bash
# Tilføj ny package
uv add package_name

# Fjern package
uv remove package_name

# Opdater alle packages
uv sync --upgrade

# Deaktivér virtual environment
deactivate
```

---

## .gitignore

For at undgå at uønskede filer bliver inkluderet i versionkontrol:

```bash
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
