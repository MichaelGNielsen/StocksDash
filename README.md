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


### købs og salgs regler

Her er en klar opstilling af reglerne, som de er defineret i din kode, samt et svar på, hvordan du skal forholde dig til aktier, der vender nede fra bunden.

---

## 🟢 Regler for KØB (Entry)

For at systemet genererer et købssignal, skal **alle** følgende betingelser være opfyldt samtidigt:

1. **Perfect Order (Trend-stakken):**
* SMA 5 skal være over SMA 10.
* SMA 10 skal være over SMA 20.
* *Samtidig* skal alle tre gennemsnit (5, 10 og 20) være stigende (højere i dag end i går).


2. **Langsigtet Filter:**
* Kursen skal ligge **over SMA 200**. Dette sikrer, at du ikke køber en aktie, der er i en overordnet nedtrend.


3. **Breakout / Styrke:**
* Kursen skal være tæt på eller over sin **20-dages High**. Det beviser, at der er frisk momentum og nye købere.


4. **Sikkerhedsfilter (Extension):**
* Kursen må **ikke være steget for hurtigt**. Den skal ligge mindre end **8%** over SMA 20. Hvis den er strukket mere end det, venter systemet på en lille pause (pullback), før den giver signal.



---

## 🔴 Regler for SALG (Exit)

Systemet er designet til at få dig ud hurtigt, når trenden svækkes. Der gives salgssignal, hvis blot **én** af disse ting sker:

1. **Trend-brud (Hurtig):**
* SMA 5 krydser under SMA 10. Dette er det første tegn på, at momentum forsvinder.


2. **Trend-brud (Kritisk):**
* Kursen lukker **under SMA 20**. Når prisen bryder SMA 20, betragtes den kortsigtede optrend som afsluttet.



---

## ❓ Hvad hvis aktien er under SMA 50 og 200 og begynder at gå op?

Dette scenarie kaldes ofte for et **"Bottom Reversal"** (bundvending). Selvom det ser fristende ud at købe billigt helt nede i bunden, er det her, de fleste "traders" brænder fingrene.

### Er det et godt tidspunkt at købe?

**Nej, ikke med det samme.** En aktie under SMA 200 er statistisk set i en "bjørnemarked"-fase. Mange aktier begynder at gå op, kun for at ramme SMA 50 eller 200 som en mur (modstand) og derefter falde til nye bunde.

### Hvornår skal man så købe?

Hvis du vil bruge din "Perfect Order" strategi sikkert, skal du vente på **"The Turn"**:

1. **Vind over gennemsnittene:** Vent til kursen bryder op over SMA 50. Det viser, at den mellemlange trend vender.
2. **Etablering af bund:** Vent på at SMA 20 begynder at pege opad.
3. **Det gyldne punkt:** Det absolut sikreste tidspunkt i din strategi er, når kursen bryder op **over SMA 200**, og de korte gennemsnit (5, 10, 20) lægger sig i "Perfect Order" ovenover.

**Konklusion:** At købe mens den er under SMA 200 er at "gætte" på bunden. At købe når den er over SMA 200 (som din kode kræver) er at "bekræfte" trenden.

*Vil du have mig til at tilføje en "Watchlist" funktion i koden, der markerer aktier, som er ved at vende bunden, men som endnu ikke er gået i Køb?*

### trendline breakout
Det du beskriver, er en af de mest klassiske og kraftfulde strategier inden for teknisk analyse. Når en aktie har været faldende og pludselig bryder ud af sin negative retning, kaldes det typisk et **Trendline Breakout** eller en **Trend Reversal** (trendvending).

Her er en gennemgang af, hvad reglen hedder, og hvordan den fungerer i praksis:

---

## 📈 Trendline Breakout (Trendlinje-brud)

Denne regel fokuserer på at tegne en linje hen over de "toppe", aktien har lavet, mens den faldt. Så længe prisen er under linjen, er trenden negativ.

### Hvordan den virker:

1. **Identifikation:** Man finder mindst 2 eller 3 faldende toppe og forbinder dem med en ret linje (en faldende trendlinje).
2. **Bruddet (The Break):** Når aktien lukker **over** denne linje, er det et tegn på, at sælgerne har mistet kontrollen, og køberne har overtaget.
3. **Volumen:** Et ægte trend-brud bør ske med høj volumen (mange handler). Det bekræfter, at bruddet er "ægte" og ikke bare en midlertidig svingning.

---

## 🧱 Andre navne for samme fænomen

Afhængig af hvilket mønster aktien danner, mens den bryder trenden, kaldes det også:

### 1. Falling Wedge (Faldende kile)

Her snævrer kursen ind, mens den falder. Det ligner en tragt, der peger nedad. Når prisen bryder ud af den øverste linje, ses det som et meget stærkt købssignal, fordi energien er blevet "presset sammen" og nu udløses opad.

### 2. Double Bottom (Dobbeltbund)

Aktien falder til et vist punkt, stiger lidt, falder tilbage til samme punkt (men ikke under) og bryder derefter op. Det ligner et **"W"**. Bruddet sker, når midterpunktet i W'et passeres.

### 3. Change of Character (ChoCh)

Inden for moderne "Smart Money" trading kalder man det et *Change of Character*. Det sker, når aktien holder op med at lave "Lower Highs" (lavere toppe) og i stedet laver sin første "Higher High" (højere top).

---

## 🛠 Hvordan kan det bruges i din kode?

Hvis vi skal indkode dette, kigger man typisk på **Donchian Channels** eller **Price Channels**.

* **Reglen:** Hvis prisen bryder ud over det højeste punkt i de sidste 20-50 dage (efter en længere periode med fald), så har vi et trendlinje-brud.
* **I din nuværende strategi:** Du har allerede en del af dette med din `20d_high` regel! Når aktien har været faldende, vil dens 20-dages high ligge ret lavt. Så snart den bryder det niveau, har du teknisk set et breakout fra den korte trend.

---

## 💡 Er det et stærkt signal?

**Ja, men med et forbehold:** Et brud på en faldende trendlinje er stærkest, hvis det sker i bunden af en langvarig korrektion. Det er ofte her, de store institutionelle investorer begynder at købe op.

**Opsummering af købsreglen for Trend-brud:**

* **Før:** Aktier laver lavere toppe og lavere bunde.
* **Signal:** Prisen bryder over den seneste top (Breakout).
* **Bekræftelse:** Prisen holder sig over det tidligere modstandsniveau (nu kaldet support).

Vil du have mig til at tilføje en logik i din kode, der specifikt kigger efter, om en aktie har været faldende i f.eks. 30 dage og nu bryder op over sin SMA 50 som tegn på et trend-brud?
