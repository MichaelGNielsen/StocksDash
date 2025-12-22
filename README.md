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
uv run python main.py --debug
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

## 📈 Trading Strategi: SMA Perfect Order (3-6 mdr. horisont)

Dette program anvender en trend-følgende strategi baseret på "Moving Average Stacking" og momentum. Strategien er designet til mellemlange trends (3-6 måneder) og fokuserer på at købe aktier med stærk acceleration og beskytte profitten med et glidende stop-loss.

### 🛠 Tekniske Indikatorer

* **SMA 5 (Hurtig):** Fanger det helt korte momentum.
* **SMA 10 (Medium):** Bekræfter retningen.
* **SMA 20 (Trend-base):** Fungerer som den primære støtte og grundlag for stop-loss.
* **SMA 200 (Filter):** Den langsigtede trend-indikator. Prisen skal være over denne for at tillade køb.
* **ATR (14):** Bruges til at beregne en buffer for stop-loss (volatilitet).

---

### 🟢 Købssignaler (Entry)

For at udløse et købssignal skal følgende betingelser være opfyldt samtidig:

1. **Pris-filter:** Prisen skal lukke over **SMA 200**.
2. **Perfect Order (The Stack):** SMA 5 skal være over SMA 10, og SMA 10 skal være over SMA 20 (`SMA 5 > SMA 10 > SMA 20`).
3. **Momentum (Optrending):** SMA 5 skal have en positiv hældning (værdien i dag er højere end i går).
4. **Bekræftelse:** Prisen skal lukke over SMA 5.

---

### 🔴 Salgssignaler (Exit & Stop Loss)

Strategien bruger to typer udgange for at minimere risiko:

1. **Trend-brud:** Hvis den hurtige trend knækker (`SMA 5 < SMA 10`).
2. **Trailing Stop Loss:** Hvis prisen lukker under det glidende sikkerhedsnet.
   * **Stop-niveau:** `SMA 20 - (0.5 * ATR)`.
   * *Dette giver aktien plads til naturlig volatilitet, men lukker positionen hvis den dykker for dybt.*

---

### 📋 Strategiens Logik (Opsummering)

| Tilstand | Handling | Forklaring |
| :--- | :--- | :--- |
| **Bullish Stack** | **Køb / Hold** | Alle gennemsnit peger op og ligger i korrekt rækkefølge. |
| **SMA 5 under 10** | **Advarsel / Sælg** | Momentum er aftagende. Overvej at tage profit. |
| **Pris under Stop** | **Sælg nu** | Trenden anses for afsluttet eller risikoen er for høj. |

---

## 🚀 Avanceret Strategi: "Extension Filter" (Med Pullback-Regel)

For at undgå at købe på toppen af stærke ryk, tilbyder strategien nu et **sikkerhedsfilter** baseret på hvor langt prisen er fra SMA 20.

### 📏 Extension (Stretch) — Måling af Afstand

**Extension i procent** = `((Pris - SMA 20) / SMA 20) * 100`

Dette tal forteller hvor mange procent prisen ligger over eller under SMA 20:
- **Extension = 0%:** Prisen er lige på SMA 20 (ingen afstand).
- **Extension = 2%:** Prisen er 2% over SMA 20 (moderat afstand).
- **Extension = 5%:** Prisen er 5% over SMA 20 (god afstand — dette er grænsværdien).
- **Extension = 8%:** Prisen er 8% over SMA 20 (STRETCH — risikabelt at købe her).

### 🛡️ Avanceret Kaufsignal med Sikkerhedsfilter

Køb kun når **ALT** dette er sandt:

1. **Perfect Order:** `SMA 5 > SMA 10 > SMA 20` ✅
2. **Langsigtet Filter:** `Pris > SMA 200` ✅
3. **Sikkerhedsfilter:** `Extension < 5%` ✅ (Aktien er ikke "strakt")

Hvis Perfect Order er der, men Extension ≥ 5%, venter vi på et **pullback** (lille dyk ned mod SMA 20).

### 📊 Signal-Beskeder (get_advanced_trade_signals)

Funktionen `get_advanced_trade_signals(df)` returnerer:

- **🚀 KØB NU:** Perfect Order + Pris > SMA 200 + Extension < 5%

  ```
  🚀 KØB NU: Perfekt setup og prisen er kun 2.3% over SMA 20.
  ```

- **🟡 AFVENT:** Perfect Order men Extension ≥ 5%
  ```
  🟡 AFVENT: Trenden er stærk, men aktien er 'strakt' (7.2%). Vent på et lille dyk (pullback).
  ```

- **🛑 SÆLG:** Trend-brud eller pris under SMA 20
  ```
  🛑 SÆLG: Trenden er brudt.
  ```
