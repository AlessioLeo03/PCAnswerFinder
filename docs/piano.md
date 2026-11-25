# Cerchia e Chiedi — Piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Programma Windows che, tenendo premuto Win, congela lo schermo, permette di cerchiare/evidenziare/cliccare e manda la selezione in una chat nuova dell'app desktop di Claude.

**Architecture:** Applicazione PySide6 senza finestra principale (solo icona di notifica). Un hook di tastiera a basso livello riconosce la pressione lunga di Win; uno strato a tutto schermo per monitor mostra la foto congelata e gestisce i gesti; la selezione viene incollata nell'app di Claude simulando tastiera e appunti. La logica pura (stato del tasto, gesti, messaggio) è separata e coperta da prove automatiche.

**Tech Stack:** Python 3.12, PySide6, winrt (Windows.Media.Ocr), uiautomation, ctypes, pytest.

**Spec:** `C:\sviluppo\cerchia-e-chiedi\docs\specifica.md`

## Global Constraints

- Mai creare file, cartelle, moduli o classi il cui nome contenga "conti" (regola di rete di `C:\sviluppo\CLAUDE.md`).
- Python 3.12, Windows 11, ambiente virtuale in `C:\sviluppo\cerchia-e-chiedi\.venv`.
- Soglia pressione lunga Win: 500 ms. Soglia clic: 6 px. Margine tratto: 12 px. Margine testo: 8 px. Minimo riquadro: 32 × 32 px.
- Le foto dello schermo restano in memoria: mai scritte su disco.
- Tutti i testi dell'interfaccia in italiano, esattamente come scritti in questo piano.
- La cartella non è un repository git: nessun passo di commit. Al posto del commit, ogni task termina con l'esecuzione delle prove.
- Il download delle librerie (Task 1) richiede il permesso esplicito dell'utente prima di eseguire `pip install`.
- Tutti i comandi si eseguono da `C:\sviluppo\cerchia-e-chiedi` in PowerShell.

## Struttura dei file

```
cerchia-e-chiedi\
  avvia.pyw                 avvio senza console (usato da "Avvia con Windows")
  pyproject.toml            configurazione pytest
  requisiti.txt             librerie
  cerchia\
    __init__.py
    impostazioni.py         costanti regolabili (percorso Claude, metodo chat nuova, attese)
    stato_win.py            macchina a stati del tasto Win (pura)
    gesti.py                Rett, Parola, classificazione gesti, riquadri, parole (pura)
    messaggio.py            testo da mandare a Claude (pura)
    tastiera.py             SendInput con marca riconoscibile
    tasto_win.py            hook WH_KEYBOARD_LL + timer → segnale "avvia"
    cattura.py              foto degli schermi, ritaglio PNG
    ocr.py                  OCR di Windows in un thread
    elementi.py             elemento UI Automation sotto un punto
    schermata.py            strato a tutto schermo + Sessione multi-monitor
    appunti.py              salva/ripristina appunti, immagine/testo
    invio_claude.py         trova/attiva Claude, chat nuova, incolla, invia
    avvio.py                icona di notifica, collegamenti, avvio con Windows
  tests\
    test_stato_win.py
    test_gesti.py
    test_messaggio.py
    test_ocr.py
  docs\
    specifica.md
    piano.md
    prove-a-mano.md
```

---

### Task 1: Ambiente e scheletro del progetto

**Files:**
- Create: `requisiti.txt`, `pyproject.toml`, `cerchia\__init__.py`, `tests\__init__.py`

**Interfaces:**
- Produces: ambiente `.venv` con le librerie; pacchetto `cerchia` importabile dalle prove.

- [ ] **Step 1: Chiedere il permesso all'utente** per scaricare con pip: PySide6, i pacchetti winrt elencati sotto, uiautomation, pytest (circa 100 MB, da PyPI). Procedere solo dopo un sì esplicito.

- [ ] **Step 2: Creare `requisiti.txt`**

```
PySide6>=6.7
winrt-runtime>=2.0
winrt-Windows.Foundation>=2.0
winrt-Windows.Foundation.Collections>=2.0
winrt-Windows.Globalization>=2.0
winrt-Windows.Graphics.Imaging>=2.0
winrt-Windows.Media.Ocr>=2.0
winrt-Windows.Storage.Streams>=2.0
uiautomation>=2.0
pytest>=8
```

- [ ] **Step 3: Creare `pyproject.toml`**

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 4: Creare `cerchia\__init__.py` e `tests\__init__.py`** vuoti.

- [ ] **Step 5: Creare l'ambiente e installare**

Run:
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requisiti.txt
```
Expected: installazione completata senza errori.

- [ ] **Step 6: Verificare gli import**

Run: `.\.venv\Scripts\python -c "import PySide6, uiautomation; from winrt.windows.media.ocr import OcrEngine; print('ok')"`
Expected: `ok`

---

### Task 2: Verifica preliminare — chat nuova nell'app di Claude

**Files:**
- Create: `cerchia\impostazioni.py`

**Interfaces:**
- Produces: `impostazioni.CHAT_NUOVA: tuple[str, object]` — `("tasti", [vk, ...])`, `("link", "url")` oppure `("nessuno", None)`; `CLAUDE_EXE: str`; `ATTESA_AVVIO_MS`, `ATTESA_CHAT_NUOVA_MS`, `ATTESA_CARICAMENTO_MS: int`.

Questa sessione di lavoro gira dentro l'app desktop di Claude: le prove cambiano la schermata dell'app. Per questo le esegue l'utente a mano.

- [ ] **Step 1: Chiedere all'utente di provare, nell'app desktop di Claude, uno alla volta:**
  1. `Ctrl + Shift + O`
  2. `Ctrl + N`
  3. il comando `Start-Process "claude://claude.ai/new"` in PowerShell

  e di dire quale apre una chat nuova (scheda Chat, casella di testo pronta).

- [ ] **Step 2: Creare `cerchia\impostazioni.py`** mettendo in `CHAT_NUOVA` il primo metodo che ha funzionato. Esempio con `Ctrl + Shift + O`:

```python
"""Costanti regolabili di Cerchia e Chiedi."""

# Programma che apre l'app desktop di Claude
CLAUDE_EXE = r"%LOCALAPPDATA%\AnthropicClaude\claude.exe"

# Come aprire una chat nuova nell'app di Claude (deciso nel Task 2 del piano):
#   ("tasti", [codici VK in ordine di pressione])
#   ("link", "indirizzo claude://...")
#   ("nessuno", None)  -> si usa la chat aperta
VK_CONTROL, VK_SHIFT = 0x11, 0x10
CHAT_NUOVA: tuple[str, object] = ("tasti", [VK_CONTROL, VK_SHIFT, ord("O")])

# Attese in millisecondi
ATTESA_AVVIO_MS = 2500        # dopo l'apertura dell'app
ATTESA_CHAT_NUOVA_MS = 800    # dopo il comando "chat nuova"
ATTESA_CARICAMENTO_MS = 1500  # dopo aver incollato l'immagine
```

Se nessun metodo funziona: `CHAT_NUOVA = ("nessuno", None)`.

---

### Task 3: Macchina a stati del tasto Win

**Files:**
- Create: `cerchia\stato_win.py`
- Test: `tests\test_stato_win.py`

**Interfaces:**
- Produces: `VK_LWIN`, `VK_RWIN`, `SOGLIA_MS`; `Stato` (enum RIPOSO/ATTESA/AVVIATO/COMBINAZIONE); `Esito(blocca: bool, reinvia: list[tuple[int, bool]], avvia: bool)`; `StatoWin(soglia_ms=500)` con `tasto(vk: int, giu: bool, ora_ms: int) -> Esito`, `tempo(ora_ms: int) -> bool`, attributo `stato`.

- [ ] **Step 1: Scrivere le prove**

```python
from cerchia.stato_win import VK_LWIN, Stato, StatoWin

VK_E = 0x45


def test_pressione_breve_riapre_start():
    s = StatoWin()
    assert s.tasto(VK_LWIN, True, 0).blocca
    esito = s.tasto(VK_LWIN, False, 200)
    assert esito.blocca
    assert esito.reinvia == [(VK_LWIN, True), (VK_LWIN, False)]
    assert s.stato is Stato.RIPOSO


def test_pressione_lunga_avvia_e_blocca_rilascio():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    assert not s.tempo(499)
    assert s.tempo(500)
    esito = s.tasto(VK_LWIN, False, 900)
    assert esito.blocca and esito.reinvia == [] and not esito.avvia
    assert s.stato is Stato.RIPOSO


def test_ripetizione_automatica_oltre_soglia_avvia():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    esito = s.tasto(VK_LWIN, True, 530)
    assert esito.avvia and esito.blocca
    assert s.stato is Stato.AVVIATO


def test_combinazione_win_e_passa():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    esito = s.tasto(VK_E, True, 100)
    assert esito.blocca
    assert esito.reinvia == [(VK_LWIN, True), (VK_E, True)]
    assert not s.tasto(VK_E, False, 150).blocca
    assert not s.tasto(VK_LWIN, False, 200).blocca
    assert s.stato is Stato.RIPOSO
    assert not s.tempo(1000)


def test_altri_tasti_a_riposo_passano():
    assert not StatoWin().tasto(VK_E, True, 0).blocca


def test_durante_avviato_altri_tasti_passano_e_win_resta_bloccato():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    s.tempo(600)
    assert not s.tasto(VK_E, True, 700).blocca
    assert s.tasto(VK_LWIN, True, 710).blocca
```

- [ ] **Step 2: Eseguire e vedere il fallimento**

Run: `.\.venv\Scripts\python -m pytest tests\test_stato_win.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cerchia.stato_win'`

- [ ] **Step 3: Scrivere `cerchia\stato_win.py`**

```python
"""Macchina a stati della pressione del tasto Win (logica pura, senza Windows)."""
from dataclasses import dataclass, field
from enum import Enum, auto

VK_LWIN = 0x5B
VK_RWIN = 0x5C
SOGLIA_MS = 500


class Stato(Enum):
    RIPOSO = auto()
    ATTESA = auto()
    AVVIATO = auto()
    COMBINAZIONE = auto()


@dataclass
class Esito:
    blocca: bool
    reinvia: list[tuple[int, bool]] = field(default_factory=list)  # (vk, giu)
    avvia: bool = False


def _e_win(vk: int) -> bool:
    return vk in (VK_LWIN, VK_RWIN)


class StatoWin:
    def __init__(self, soglia_ms: int = SOGLIA_MS) -> None:
        self.soglia_ms = soglia_ms
        self.stato = Stato.RIPOSO
        self._vk_win = VK_LWIN
        self._inizio_ms = 0

    def tasto(self, vk: int, giu: bool, ora_ms: int) -> Esito:
        if self.stato is Stato.RIPOSO:
            if _e_win(vk) and giu:
                self.stato = Stato.ATTESA
                self._vk_win = vk
                self._inizio_ms = ora_ms
                return Esito(blocca=True)
            return Esito(blocca=False)

        if self.stato is Stato.ATTESA:
            if vk == self._vk_win:
                if giu:  # ripetizione automatica del tasto tenuto premuto
                    return Esito(blocca=True, avvia=self.tempo(ora_ms))
                self.stato = Stato.RIPOSO
                return Esito(blocca=True, reinvia=[(vk, True), (vk, False)])
            if giu:
                self.stato = Stato.COMBINAZIONE
                return Esito(blocca=True, reinvia=[(self._vk_win, True), (vk, True)])
            return Esito(blocca=False)

        if self.stato is Stato.COMBINAZIONE:
            if vk == self._vk_win and not giu:
                self.stato = Stato.RIPOSO
            return Esito(blocca=False)

        # Stato.AVVIATO
        if vk == self._vk_win:
            if not giu:
                self.stato = Stato.RIPOSO
            return Esito(blocca=True)
        return Esito(blocca=False)

    def tempo(self, ora_ms: int) -> bool:
        """Da chiamare con un timer: True se la pressione è appena diventata lunga."""
        if self.stato is Stato.ATTESA and ora_ms - self._inizio_ms >= self.soglia_ms:
            self.stato = Stato.AVVIATO
            return True
        return False
```

- [ ] **Step 4: Eseguire le prove**

Run: `.\.venv\Scripts\python -m pytest tests\test_stato_win.py -v`
Expected: 6 passed

---

### Task 4: Logica dei gesti

**Files:**
- Create: `cerchia\gesti.py`
- Test: `tests\test_gesti.py`

**Interfaces:**
- Produces: `Punto = tuple[float, float]`; `Rett(x, y, w, h)` (frozen, con `destra`, `basso`, `centro`, `contiene(p)`, `unione(r)`, `allarga(m)`, `dentro(limite)`); `Parola(testo: str, rett: Rett, riga: int)`; `TipoGesto` (CLIC/TESTO/CERCHIO); `classifica(punti, parole) -> TipoGesto`; `indice_parola(p, parole) -> int | None`; `indice_parola_vicina(p, parole) -> int | None`; `riquadro_da_tratto(punti, limite) -> Rett`; `parole_tra(parole, i, j) -> list[Parola]`; `parole_dentro(parole, r) -> list[Parola]`; `riquadro_parole(parole, limite) -> Rett`; `testo_di(parole) -> str`; `sposta_angolo(r, angolo, p, limite) -> Rett`. Tutte le coordinate sono pixel fisici locali allo schermo.

- [ ] **Step 1: Scrivere le prove**

```python
from cerchia.gesti import (
    Parola, Rett, TipoGesto, classifica, indice_parola_vicina, parole_dentro,
    parole_tra, riquadro_da_tratto, riquadro_parole, sposta_angolo, testo_di,
)

SCHERMO = Rett(0, 0, 1920, 1080)
PAROLE = [
    Parola("Ciao", Rett(100, 100, 80, 30), 0),
    Parola("mondo", Rett(190, 100, 100, 30), 0),
    Parola("seconda", Rett(100, 150, 120, 30), 1),
    Parola("riga", Rett(230, 150, 70, 30), 1),
]


def test_clic_se_movimento_piccolo():
    assert classifica([(500, 500), (503, 502), (501, 499)], PAROLE) is TipoGesto.CLIC


def test_testo_se_parte_su_parola_e_resta_sulla_riga():
    assert classifica([(110, 115), (200, 118), (280, 112)], PAROLE) is TipoGesto.TESTO


def test_cerchio_se_parte_fuori_dalle_parole():
    punti = [(400, 400), (600, 400), (600, 600), (400, 600)]
    assert classifica(punti, PAROLE) is TipoGesto.CERCHIO


def test_cerchio_se_parte_su_parola_ma_scende_in_verticale():
    assert classifica([(110, 115), (120, 300)], PAROLE) is TipoGesto.CERCHIO


def test_riquadro_da_tratto_con_margine():
    assert riquadro_da_tratto([(400, 400), (600, 450), (500, 600)], SCHERMO) == Rett(388, 388, 224, 224)


def test_riquadro_limitato_ai_bordi():
    r = riquadro_da_tratto([(2, 2), (300, 200)], SCHERMO)
    assert (r.x, r.y, r.destra, r.basso) == (0, 0, 312, 212)


def test_riquadro_dimensione_minima():
    r = riquadro_da_tratto([(500, 500), (502, 501)], SCHERMO)
    assert r.w == 32 and r.h == 32
    assert r.contiene((501, 500))


def test_parole_tra_su_due_righe_in_ordine_di_lettura():
    assert [p.testo for p in parole_tra(PAROLE, 3, 1)] == ["mondo", "seconda", "riga"]


def test_parola_vicina_quando_il_punto_e_fuori():
    assert indice_parola_vicina((320, 160), PAROLE) == 3


def test_parola_vicina_senza_parole():
    assert indice_parola_vicina((0, 0), []) is None


def test_parole_dentro_usa_il_centro():
    assert [p.testo for p in parole_dentro(PAROLE, Rett(90, 90, 160, 50))] == ["Ciao", "mondo"]


def test_testo_di_va_a_capo_tra_righe():
    assert testo_di(PAROLE) == "Ciao mondo\nseconda riga"


def test_riquadro_parole_unione_con_margine():
    assert riquadro_parole(PAROLE[:2], SCHERMO) == Rett(92, 92, 206, 46)


def test_sposta_angolo_basso_destra():
    assert sposta_angolo(Rett(100, 100, 200, 200), 3, (500, 450), SCHERMO) == Rett(100, 100, 400, 350)


def test_sposta_angolo_rispetta_minimo():
    assert sposta_angolo(Rett(100, 100, 200, 200), 0, (400, 400), SCHERMO) == Rett(268, 268, 32, 32)
```

- [ ] **Step 2: Eseguire e vedere il fallimento**

Run: `.\.venv\Scripts\python -m pytest tests\test_gesti.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cerchia.gesti'`

- [ ] **Step 3: Scrivere `cerchia\gesti.py`**

```python
"""Logica pura dei gesti: classificazione, riquadri e selezione delle parole.

Tutte le coordinate sono pixel fisici, relativi all'angolo in alto a sinistra dello schermo.
"""
from dataclasses import dataclass
from enum import Enum, auto
from math import hypot

Punto = tuple[float, float]

SOGLIA_CLIC_PX = 6
MARGINE_TRATTO = 12
MARGINE_TESTO = 8
MINIMO_PX = 32


@dataclass(frozen=True)
class Rett:
    x: float
    y: float
    w: float
    h: float

    @property
    def destra(self) -> float:
        return self.x + self.w

    @property
    def basso(self) -> float:
        return self.y + self.h

    @property
    def centro(self) -> Punto:
        return (self.x + self.w / 2, self.y + self.h / 2)

    def contiene(self, p: Punto) -> bool:
        return self.x <= p[0] <= self.destra and self.y <= p[1] <= self.basso

    def unione(self, altro: "Rett") -> "Rett":
        x0, y0 = min(self.x, altro.x), min(self.y, altro.y)
        x1, y1 = max(self.destra, altro.destra), max(self.basso, altro.basso)
        return Rett(x0, y0, x1 - x0, y1 - y0)

    def allarga(self, m: float) -> "Rett":
        return Rett(self.x - m, self.y - m, self.w + 2 * m, self.h + 2 * m)

    def dentro(self, limite: "Rett") -> "Rett":
        x0, y0 = max(self.x, limite.x), max(self.y, limite.y)
        x1, y1 = min(self.destra, limite.destra), min(self.basso, limite.basso)
        return Rett(x0, y0, max(0, x1 - x0), max(0, y1 - y0))


@dataclass(frozen=True)
class Parola:
    testo: str
    rett: Rett
    riga: int


class TipoGesto(Enum):
    CLIC = auto()
    TESTO = auto()
    CERCHIO = auto()


def _distanza(a: Punto, b: Punto) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def indice_parola(p: Punto, parole: list[Parola]) -> int | None:
    for i, parola in enumerate(parole):
        if parola.rett.contiene(p):
            return i
    return None


def indice_parola_vicina(p: Punto, parole: list[Parola]) -> int | None:
    if not parole:
        return None
    i = indice_parola(p, parole)
    if i is not None:
        return i
    return min(range(len(parole)), key=lambda k: _distanza(p, parole[k].rett.centro))


def classifica(punti: list[Punto], parole: list[Parola]) -> TipoGesto:
    inizio = punti[0]
    if max(_distanza(inizio, q) for q in punti) < SOGLIA_CLIC_PX:
        return TipoGesto.CLIC
    i = indice_parola(inizio, parole)
    if i is not None:
        ys = [q[1] for q in punti]
        if max(ys) - min(ys) < 1.5 * parole[i].rett.h:
            return TipoGesto.TESTO
    return TipoGesto.CERCHIO


def _con_minimo(r: Rett, minimo: float) -> Rett:
    w, h = max(r.w, minimo), max(r.h, minimo)
    cx, cy = r.centro
    return Rett(cx - w / 2, cy - h / 2, w, h)


def riquadro_da_tratto(punti: list[Punto], limite: Rett) -> Rett:
    xs = [q[0] for q in punti]
    ys = [q[1] for q in punti]
    r = Rett(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).allarga(MARGINE_TRATTO)
    return _con_minimo(r, MINIMO_PX).dentro(limite)


def parole_tra(parole: list[Parola], i: int, j: int) -> list[Parola]:
    a, b = sorted((i, j))
    return parole[a:b + 1]


def parole_dentro(parole: list[Parola], r: Rett) -> list[Parola]:
    return [p for p in parole if r.contiene(p.rett.centro)]


def riquadro_parole(parole: list[Parola], limite: Rett) -> Rett:
    r = parole[0].rett
    for p in parole[1:]:
        r = r.unione(p.rett)
    return r.allarga(MARGINE_TESTO).dentro(limite)


def testo_di(parole: list[Parola]) -> str:
    righe: list[list[str]] = []
    ultima = None
    for p in parole:
        if p.riga != ultima:
            righe.append([])
            ultima = p.riga
        righe[-1].append(p.testo)
    return "\n".join(" ".join(r) for r in righe)


def sposta_angolo(r: Rett, angolo: int, p: Punto, limite: Rett) -> Rett:
    """Sposta un angolo del riquadro. angolo: 0 alto-sx, 1 alto-dx, 2 basso-sx, 3 basso-dx."""
    x0, y0, x1, y1 = r.x, r.y, r.destra, r.basso
    px = min(max(p[0], limite.x), limite.destra)
    py = min(max(p[1], limite.y), limite.basso)
    if angolo in (0, 2):
        x0 = min(px, x1 - MINIMO_PX)
    else:
        x1 = max(px, x0 + MINIMO_PX)
    if angolo in (0, 1):
        y0 = min(py, y1 - MINIMO_PX)
    else:
        y1 = max(py, y0 + MINIMO_PX)
    return Rett(x0, y0, x1 - x0, y1 - y0)
```

- [ ] **Step 4: Eseguire le prove**

Run: `.\.venv\Scripts\python -m pytest tests\test_gesti.py -v`
Expected: 15 passed

---

### Task 5: Messaggio per Claude

**Files:**
- Create: `cerchia\messaggio.py`
- Test: `tests\test_messaggio.py`

**Interfaces:**
- Produces: `DOMANDA_VUOTA`, `TRADUCI_TESTO`, `TRADUCI_IMMAGINE: str`; `componi(domanda: str, testo: str, traduci: bool = False) -> str`.

- [ ] **Step 1: Scrivere le prove**

```python
from cerchia.messaggio import DOMANDA_VUOTA, TRADUCI_IMMAGINE, componi


def test_domanda_senza_testo():
    assert componi("Che cos'è?", "") == "Che cos'è?"


def test_domanda_con_testo():
    assert componi("Spiega", "a b") == "Spiega\n\nTesto selezionato:\n«a b»"


def test_casella_vuota():
    assert componi("   ", "") == DOMANDA_VUOTA
    assert DOMANDA_VUOTA == "Cosa c'è in questa immagine? Spiegamelo."


def test_casella_vuota_con_testo():
    assert componi("", "x") == DOMANDA_VUOTA + "\n\nTesto selezionato:\n«x»"


def test_traduci_con_testo_ignora_la_domanda():
    assert componi("ignorata", "Hello", traduci=True) == "Traduci in italiano questo testo:\n«Hello»"


def test_traduci_senza_testo():
    assert componi("", "", traduci=True) == TRADUCI_IMMAGINE
    assert TRADUCI_IMMAGINE == "Traduci in italiano il testo che vedi nell'immagine."
```

- [ ] **Step 2: Eseguire e vedere il fallimento**

Run: `.\.venv\Scripts\python -m pytest tests\test_messaggio.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cerchia.messaggio'`

- [ ] **Step 3: Scrivere `cerchia\messaggio.py`**

```python
"""Composizione del testo da mandare a Claude insieme all'immagine."""

DOMANDA_VUOTA = "Cosa c'è in questa immagine? Spiegamelo."
TRADUCI_TESTO = "Traduci in italiano questo testo:"
TRADUCI_IMMAGINE = "Traduci in italiano il testo che vedi nell'immagine."


def componi(domanda: str, testo: str, traduci: bool = False) -> str:
    domanda = domanda.strip()
    testo = testo.strip()
    if traduci:
        return f"{TRADUCI_TESTO}\n«{testo}»" if testo else TRADUCI_IMMAGINE
    base = domanda or DOMANDA_VUOTA
    if testo:
        return f"{base}\n\nTesto selezionato:\n«{testo}»"
    return base
```

- [ ] **Step 4: Eseguire le prove**

Run: `.\.venv\Scripts\python -m pytest tests\test_messaggio.py -v`
Expected: 6 passed

---

### Task 6: Hook del tasto Win e icona di notifica

**Files:**
- Create: `cerchia\tastiera.py`, `cerchia\tasto_win.py`, `cerchia\avvio.py` (prima versione)

**Interfaces:**
- Consumes: `StatoWin`, `Stato`, `SOGLIA_MS` (Task 3).
- Produces: `tastiera.MARCA: int`; `tastiera.invia(eventi: list[tuple[int, bool]]) -> None`; `tastiera.combinazione(*vks: int) -> None`; `tasto_win.TastoWin(QObject)` con segnale `avvia`, metodi `attiva()` e `disattiva()`; `avvio.main()`.

- [ ] **Step 1: Scrivere `cerchia\tastiera.py`**

```python
"""Invio di tasti simulati con SendInput, marcati per essere riconosciuti dall'hook."""
import ctypes
from ctypes import wintypes

MARCA = 0x43434843  # valore in dwExtraInfo dei tasti inviati da Cerchia e Chiedi

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
# Tasti che Windows considera "estesi"
ESTESI = {0x5B, 0x5C, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E}

ULONG_PTR = wintypes.WPARAM


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _UNIONE(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _UNIONE)]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
_user32.SendInput.restype = wintypes.UINT


def invia(eventi: list[tuple[int, bool]]) -> None:
    """eventi: lista di (codice VK, True = premuto / False = rilasciato)."""
    if not eventi:
        return
    arr = (INPUT * len(eventi))()
    for i, (vk, giu) in enumerate(eventi):
        flag = 0 if giu else KEYEVENTF_KEYUP
        if vk in ESTESI:
            flag |= KEYEVENTF_EXTENDEDKEY
        arr[i].type = INPUT_KEYBOARD
        arr[i].u.ki = KEYBDINPUT(vk, 0, flag, 0, MARCA)
    _user32.SendInput(len(eventi), arr, ctypes.sizeof(INPUT))


def combinazione(*vks: int) -> None:
    """Preme i tasti nell'ordine dato e li rilascia in ordine inverso (es. Ctrl+V)."""
    invia([(v, True) for v in vks] + [(v, False) for v in reversed(vks)])
```

- [ ] **Step 2: Scrivere `cerchia\tasto_win.py`**

```python
"""Hook di tastiera a basso livello: riconosce la pressione lunga del tasto Win."""
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QObject, QTimer, Signal

from cerchia import tastiera
from cerchia.stato_win import SOGLIA_MS, Stato, StatoWin

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", wintypes.WPARAM)]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
_user32.SetWindowsHookExW.restype = wintypes.HHOOK
_user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
_user32.CallNextHookEx.restype = LRESULT
_user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
_kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
_kernel32.GetModuleHandleW.restype = wintypes.HMODULE
_kernel32.GetTickCount.restype = wintypes.DWORD


class TastoWin(QObject):
    avvia = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._stato = StatoWin()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(SOGLIA_MS)
        self._timer.timeout.connect(self._scaduto)
        self._proc = HOOKPROC(self._callback)  # riferimento tenuto vivo
        self._hook = None

    def attiva(self) -> None:
        self._hook = _user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, _kernel32.GetModuleHandleW(None), 0)
        if not self._hook:
            raise OSError(ctypes.get_last_error(), "SetWindowsHookExW non riuscito")

    def disattiva(self) -> None:
        if self._hook:
            _user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    def _callback(self, n_code: int, w_param: int, l_param: int) -> int:
        try:
            if n_code == 0:
                k = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if k.dwExtraInfo != tastiera.MARCA:
                    giu = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                    prima = self._stato.stato
                    esito = self._stato.tasto(k.vkCode, giu, k.time)
                    if prima is not Stato.ATTESA and self._stato.stato is Stato.ATTESA:
                        self._timer.start()
                    if esito.reinvia:
                        eventi = list(esito.reinvia)
                        QTimer.singleShot(0, lambda: tastiera.invia(eventi))
                    if esito.avvia:
                        QTimer.singleShot(0, self.avvia.emit)
                    if esito.blocca:
                        return 1
        except Exception:  # l'hook non deve mai bloccare la tastiera
            pass
        return _user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _scaduto(self) -> None:
        if self._stato.tempo(_kernel32.GetTickCount()):
            self.avvia.emit()
```

- [ ] **Step 3: Scrivere la prima versione di `cerchia\avvio.py`**

```python
"""Avvio di Cerchia e Chiedi: icona di notifica e collegamento dei pezzi."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from cerchia.tasto_win import TastoWin

TITOLO = "Cerchia e Chiedi"


def _icona() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(217, 119, 87), 8))
    p.drawEllipse(10, 10, 44, 44)
    p.end()
    return QIcon(pix)


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icona = QSystemTrayIcon(_icona())
    icona.setToolTip(f"{TITOLO} — tieni premuto Win")
    menu = QMenu()
    esci = QAction("Esci", menu)
    esci.triggered.connect(app.quit)
    menu.addAction(esci)
    icona.setContextMenu(menu)
    icona.show()

    tasto = TastoWin()
    tasto.avvia.connect(lambda: icona.showMessage(TITOLO, "Pressione lunga di Win riconosciuta."))
    tasto.attiva()
    app.aboutToQuit.connect(tasto.disattiva)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Prova a mano dell'hook**

Run: `.\.venv\Scripts\python -m cerchia.avvio`
Verificare con l'utente:
- pressione breve di Win → si apre Start;
- Win + E → si apre Esplora file;
- Win tenuto premuto → notifica "Pressione lunga di Win riconosciuta." e Start NON si apre;
- "Esci" dal menu dell'icona chiude il programma.

- [ ] **Step 5: Eseguire tutte le prove automatiche**

Run: `.\.venv\Scripts\python -m pytest -v`
Expected: 27 passed

---

### Task 7: Cattura degli schermi e OCR

**Files:**
- Create: `cerchia\cattura.py`, `cerchia\ocr.py`
- Test: `tests\test_ocr.py`

**Interfaces:**
- Consumes: `Rett`, `Parola` (Task 4).
- Produces: `cattura.Foto(schermo: QScreen, immagine: QImage, origine: tuple[int, int], dpr: float)` — `immagine` in pixel fisici con devicePixelRatio 1, `origine` = angolo dello schermo in pixel fisici del desktop; `cattura.fotografa() -> list[Foto]`; `cattura.png_da_immagine(img: QImage) -> bytes`; `cattura.ritaglio_png(img: QImage, r: Rett) -> bytes`; `ocr.leggi(png: bytes) -> list[Parola] | None` (None = OCR non disponibile); `ocr.LettoreOcr(QObject)` con segnale `pronto(object)` e metodo `avvia(img: QImage)`.

- [ ] **Step 1: Scrivere la prova dell'OCR**

```python
import threading

import pytest
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter

from cerchia import ocr
from cerchia.cattura import png_da_immagine


@pytest.fixture(scope="module")
def app():
    return QGuiApplication.instance() or QGuiApplication([])


def test_legge_parole_con_posizione(app):
    img = QImage(700, 140, QImage.Format_RGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    font = QFont("Segoe UI")
    font.setPixelSize(56)
    p.setFont(font)
    p.setPen(QColor("black"))
    p.drawText(20, 95, "Ciao mondo")
    p.end()
    png = png_da_immagine(img)

    risultato = {}
    t = threading.Thread(target=lambda: risultato.update(parole=ocr.leggi(png)))
    t.start()
    t.join(30)

    parole = risultato["parole"]
    assert parole is not None, "OCR di Windows non disponibile"
    assert [x.testo for x in parole] == ["Ciao", "mondo"]
    assert all(x.riga == 0 for x in parole)
    assert parole[0].rett.x < parole[1].rett.x
```

- [ ] **Step 2: Eseguire e vedere il fallimento**

Run: `.\.venv\Scripts\python -m pytest tests\test_ocr.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cerchia.ocr'`

- [ ] **Step 3: Scrivere `cerchia\cattura.py`**

```python
"""Foto di tutti gli schermi in pixel fisici e ritagli PNG (solo in memoria)."""
import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRect
from PySide6.QtGui import QGuiApplication, QImage, QScreen

from cerchia.gesti import Rett


@dataclass
class Foto:
    schermo: QScreen
    immagine: QImage          # pixel fisici, devicePixelRatio = 1
    origine: tuple[int, int]  # angolo in alto a sinistra, pixel fisici del desktop
    dpr: float


class _MONITORINFOEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD), ("szDevice", wintypes.WCHAR * 32)]


_MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                      ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)


def _origini_fisiche() -> dict[str, tuple[int, int]]:
    """Nome del monitor (es. \\\\.\\DISPLAY1) -> angolo in pixel fisici."""
    risultato: dict[str, tuple[int, int]] = {}

    def cb(hmon, _hdc, _rect, _lparam):
        info = _MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        if ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            risultato[info.szDevice] = (info.rcMonitor.left, info.rcMonitor.top)
        return True

    ctypes.windll.user32.EnumDisplayMonitors(None, None, _MONITORENUMPROC(cb), 0)
    return risultato


def fotografa() -> list[Foto]:
    origini = _origini_fisiche()
    foto = []
    for schermo in QGuiApplication.screens():
        img = schermo.grabWindow(0).toImage()
        img.setDevicePixelRatio(1.0)
        g = schermo.geometry()
        origine = origini.get(schermo.name(), (g.x(), g.y()))
        foto.append(Foto(schermo, img, origine, schermo.devicePixelRatio()))
    return foto


def png_da_immagine(img: QImage) -> bytes:
    dati = QByteArray()
    buf = QBuffer(dati)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    return bytes(dati.data())


def ritaglio_png(img: QImage, r: Rett) -> bytes:
    return png_da_immagine(img.copy(QRect(round(r.x), round(r.y), round(r.w), round(r.h))))
```

- [ ] **Step 4: Scrivere `cerchia\ocr.py`**

```python
"""Riconoscimento del testo con l'OCR incluso in Windows, eseguito in un thread."""
import asyncio
import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

from cerchia.cattura import png_da_immagine
from cerchia.gesti import Parola, Rett


async def _leggi(png: bytes) -> list[Parola] | None:
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

    motore = OcrEngine.try_create_from_user_profile_languages()
    if motore is None:
        return None
    flusso = InMemoryRandomAccessStream()
    scrittore = DataWriter(flusso)
    scrittore.write_bytes(png)
    await scrittore.store_async()
    scrittore.detach_stream()
    flusso.seek(0)
    decoder = await BitmapDecoder.create_async(flusso)
    bitmap = await decoder.get_software_bitmap_async()
    esito = await motore.recognize_async(bitmap)
    parole = []
    for n, riga in enumerate(esito.lines):
        for w in riga.words:
            b = w.bounding_rect
            parole.append(Parola(w.text, Rett(b.x, b.y, b.width, b.height), n))
    return parole


def leggi(png: bytes) -> list[Parola] | None:
    """Parole in ordine di lettura, oppure None se l'OCR di Windows non è disponibile."""
    try:
        return asyncio.run(_leggi(png))
    except Exception:
        return None


class LettoreOcr(QObject):
    pronto = Signal(object)  # list[Parola] | None

    def avvia(self, img: QImage) -> None:
        png = png_da_immagine(img)
        threading.Thread(target=self._lavora, args=(png,), daemon=True).start()

    def _lavora(self, png: bytes) -> None:
        parole = leggi(png)
        try:
            self.pronto.emit(parole)
        except RuntimeError:  # lo strato è già stato chiuso
            pass
```

- [ ] **Step 5: Eseguire la prova dell'OCR**

Run: `.\.venv\Scripts\python -m pytest tests\test_ocr.py -v`
Expected: 1 passed. Se fallisce con "OCR di Windows non disponibile": controllare in Impostazioni › Ora e lingua › Lingua che la lingua abbia "Riconoscimento ottico dei caratteri"; se fallisce su `write_bytes`, sostituire con `scrittore.write_bytes(list(png))` e rieseguire.

---

### Task 8: Strato a tutto schermo, gesti ed elemento sotto il clic

**Files:**
- Create: `cerchia\elementi.py`, `cerchia\schermata.py`
- Modify: `cerchia\avvio.py` (sostituire l'intero file)

**Interfaces:**
- Consumes: `Foto`, `ritaglio_png` (Task 7); `LettoreOcr` (Task 7); funzioni di `gesti` (Task 4); `componi` (Task 5); `TastoWin` (Task 6).
- Produces: `elementi.rett_elemento(x: int, y: int, da_ignorare: list[int]) -> Rett | None` (coordinate fisiche del desktop); `schermata.Sessione(foto: list[Foto], rett_elemento)` con segnali `invia(bytes, str)`, `copia(str)`, `chiusa()` e metodi `mostra()`, `chiudi()`.

- [ ] **Step 1: Scrivere `cerchia\elementi.py`**

```python
"""Elemento dell'interfaccia (UI Automation) sotto un punto dello schermo."""
import ctypes
from ctypes import wintypes

from cerchia.gesti import Rett

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x2

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
_user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
_user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
_user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD]


def rett_elemento(x: int, y: int, da_ignorare: list[int]) -> Rett | None:
    """Rettangolo (pixel fisici del desktop) dell'elemento sotto (x, y).

    Le finestre in da_ignorare (gli strati di Cerchia e Chiedi) diventano trasparenti ai clic
    per il tempo della ricerca, così UI Automation vede cosa c'è sotto.
    """
    import uiautomation as auto  # importato tardi: dopo che Qt ha impostato la gestione DPI

    vecchi = []
    for h in da_ignorare:
        stile = _user32.GetWindowLongPtrW(h, GWL_EXSTYLE)
        vecchi.append((h, stile))
        _user32.SetWindowLongPtrW(h, GWL_EXSTYLE, stile | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        if not stile & WS_EX_LAYERED:
            _user32.SetLayeredWindowAttributes(h, 0, 255, LWA_ALPHA)
    try:
        el = auto.ControlFromPoint(x, y)
        if el is None:
            return None
        r = el.BoundingRectangle
        if r.width() <= 0 or r.height() <= 0:
            return None
        return Rett(r.left, r.top, r.width(), r.height())
    except Exception:
        return None
    finally:
        for h, stile in vecchi:
            _user32.SetWindowLongPtrW(h, GWL_EXSTYLE, stile)
```

- [ ] **Step 2: Scrivere `cerchia\schermata.py`**

```python
"""Strato a tutto schermo: foto congelata, luccichio, gesti e barra della domanda."""
from collections.abc import Callable
from math import hypot

from PySide6.QtCore import QEasingCurve, QObject, QPointF, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from cerchia import gesti
from cerchia.cattura import Foto, ritaglio_png
from cerchia.gesti import Parola, Rett, TipoGesto
from cerchia.messaggio import componi
from cerchia.ocr import LettoreOcr

TrovaElemento = Callable[[int, int], Rett | None]

AZZURRO = QColor(80, 150, 255, 110)
BUIO_MAX = 110     # oscuramento senza selezione (0-255)
BUIO_FUORI = 160   # oscuramento fuori dal riquadro selezionato
RAGGIO_MANIGLIA = 24
MSG_OCR_ASSENTE = "Testo non disponibile: in Windows manca la lingua per il riconoscimento del testo."
MSG_NESSUN_ELEMENTO = "Nessun elemento qui, prova a cerchiare."

STILE = """
QFrame#barra { background: rgba(32, 33, 36, 235); border-radius: 28px; }
QLineEdit { background: transparent; border: none; color: white; font-size: 16px; padding: 0 12px; }
QPushButton { background: rgba(255, 255, 255, 30); color: white; border: none; border-radius: 18px;
              padding: 8px 14px; font-size: 14px; }
QPushButton:hover { background: rgba(255, 255, 255, 55); }
QPushButton:disabled { color: rgba(255, 255, 255, 90); }
QLabel#avviso { background: rgba(32, 33, 36, 235); color: white; border-radius: 14px;
                padding: 8px 14px; font-size: 14px; }
"""


def _qrect(r: Rett) -> QRectF:
    return QRectF(r.x, r.y, r.w, r.h)


class Schermata(QWidget):
    gesto_iniziato = Signal()
    invia = Signal(bytes, str)
    copia = Signal(str)
    esci = Signal()

    def __init__(self, foto: Foto, trova_elemento: TrovaElemento) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(foto.schermo.geometry())
        self._foto = foto
        self._trova_elemento = trova_elemento
        self._dpr = foto.dpr
        self._limite = Rett(0, 0, foto.immagine.width(), foto.immagine.height())
        self._parole: list[Parola] = []
        self._ocr = "in_corso"  # "in_corso" | "ok" | "assente"
        self._punti: list[tuple[float, float]] = []
        self._tipo: TipoGesto | None = None
        self._riquadro: Rett | None = None
        self._sel: list[Parola] = []
        self._maniglia: int | None = None
        self._buio = 0.0
        self._luce = -1.0
        self._crea_barra()
        self._crea_animazioni()
        self._lettore = LettoreOcr(self)
        self._lettore.pronto.connect(self._ocr_pronto)
        self._lettore.avvia(foto.immagine)

    # ---------- costruzione ----------

    def _crea_barra(self) -> None:
        self.setStyleSheet(STILE)
        self._barra = QFrame(self)
        self._barra.setObjectName("barra")
        riga = QHBoxLayout(self._barra)
        riga.setContentsMargins(16, 8, 8, 8)
        riga.setSpacing(8)
        self._campo = QLineEdit()
        self._campo.setPlaceholderText("Chiedi a Claude su questa selezione…")
        self._campo.returnPressed.connect(lambda: self._invia(False))
        self._btn_traduci = QPushButton("Traduci")
        self._btn_traduci.clicked.connect(lambda: self._invia(True))
        self._btn_copia = QPushButton("Copia testo")
        self._btn_copia.clicked.connect(self._copia)
        self._btn_invia = QPushButton("Invia")
        self._btn_invia.clicked.connect(lambda: self._invia(False))
        for w in (self._campo, self._btn_traduci, self._btn_copia, self._btn_invia):
            riga.addWidget(w)
        riga.setStretch(0, 1)
        self._barra.hide()
        self._avviso = QLabel(self)
        self._avviso.setObjectName("avviso")
        self._avviso.hide()

    def _crea_animazioni(self) -> None:
        self._anim_buio = QVariantAnimation(self)
        self._anim_buio.setStartValue(0.0)
        self._anim_buio.setEndValue(1.0)
        self._anim_buio.setDuration(200)
        self._anim_buio.valueChanged.connect(self._imposta_buio)
        self._anim_luce = QVariantAnimation(self)
        self._anim_luce.setStartValue(-0.3)
        self._anim_luce.setEndValue(1.3)
        self._anim_luce.setDuration(900)
        self._anim_luce.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim_luce.valueChanged.connect(self._imposta_luce)
        self._anim_luce.finished.connect(lambda: self._imposta_luce(-1.0))

    def _imposta_buio(self, v: float) -> None:
        self._buio = v
        self.update()

    def _imposta_luce(self, v: float) -> None:
        self._luce = v
        self.update()

    # ---------- interfaccia pubblica ----------

    def mostra(self, attiva: bool) -> None:
        self.show()
        self.raise_()
        if attiva:
            self.activateWindow()
        self._anim_buio.start()
        self._anim_luce.start()

    def azzera(self) -> None:
        self._punti = []
        self._tipo = None
        self._riquadro = None
        self._sel = []
        self._maniglia = None
        self._barra.hide()
        self._avviso.hide()
        self.update()

    # ---------- mouse e tastiera ----------

    def _px(self, ev) -> tuple[float, float]:
        p = ev.position()
        return (p.x() * self._dpr, p.y() * self._dpr)

    def _maniglia_vicina(self, p: tuple[float, float]) -> int | None:
        r = self._riquadro
        angoli = [(r.x, r.y), (r.destra, r.y), (r.x, r.basso), (r.destra, r.basso)]
        for i, a in enumerate(angoli):
            if hypot(p[0] - a[0], p[1] - a[1]) <= RAGGIO_MANIGLIA * self._dpr:
                return i
        return None

    def mousePressEvent(self, ev) -> None:
        if ev.button() != Qt.LeftButton:
            return
        p = self._px(ev)
        self._avviso.hide()
        if self._riquadro is not None:
            self._maniglia = self._maniglia_vicina(p)
            if self._maniglia is not None:
                return
        self.gesto_iniziato.emit()
        self.azzera()
        self._punti = [p]
        self.update()

    def mouseMoveEvent(self, ev) -> None:
        p = self._px(ev)
        if self._maniglia is not None:
            self._riquadro = gesti.sposta_angolo(self._riquadro, self._maniglia, p, self._limite)
        elif self._punti:
            self._punti.append(p)
        self.update()

    def mouseReleaseEvent(self, ev) -> None:
        if ev.button() != Qt.LeftButton:
            return
        if self._maniglia is not None:
            self._maniglia = None
            self._tipo = TipoGesto.CERCHIO
            self._aggiorna_sel()
            self._mostra_barra()
            return
        if not self._punti:
            return
        punti, self._punti = self._punti, []
        tipo = gesti.classifica(punti, self._parole)
        if tipo is TipoGesto.CLIC:
            r = self._elemento(punti[0])
            if r is None:
                self._mostra_avviso(MSG_NESSUN_ELEMENTO)
                self.update()
                return
            self._riquadro = r
        elif tipo is TipoGesto.TESTO:
            i0 = gesti.indice_parola(punti[0], self._parole)
            i1 = gesti.indice_parola_vicina(punti[-1], self._parole)
            self._sel = gesti.parole_tra(self._parole, i0, i1)
            self._riquadro = gesti.riquadro_parole(self._sel, self._limite)
        else:
            self._riquadro = gesti.riquadro_da_tratto(punti, self._limite)
        self._tipo = tipo
        if tipo is not TipoGesto.TESTO:
            self._aggiorna_sel()
        self._mostra_barra()

    def keyPressEvent(self, ev) -> None:
        if ev.key() == Qt.Key_Escape:
            self.esci.emit()
        else:
            super().keyPressEvent(ev)

    # ---------- selezione ----------

    def _elemento(self, p: tuple[float, float]) -> Rett | None:
        ox, oy = self._foto.origine
        r = self._trova_elemento(int(ox + p[0]), int(oy + p[1]))
        if r is None:
            return None
        locale = Rett(r.x - ox, r.y - oy, r.w, r.h).dentro(self._limite)
        area = locale.w * locale.h
        if area <= 0 or area > 0.9 * self._limite.w * self._limite.h:
            return None
        return locale

    def _aggiorna_sel(self) -> None:
        if self._riquadro is not None:
            self._sel = gesti.parole_dentro(self._parole, self._riquadro)
        self._aggiorna_pulsanti()

    def _ocr_pronto(self, parole: list[Parola] | None) -> None:
        if parole is None:
            self._ocr = "assente"
            self._parole = []
            if self._barra.isVisible():
                self._mostra_avviso(MSG_OCR_ASSENTE)
        else:
            self._ocr = "ok"
            self._parole = parole
            if self._riquadro is not None and self._tipo is not TipoGesto.TESTO:
                self._aggiorna_sel()
        self._aggiorna_pulsanti()

    def _aggiorna_pulsanti(self) -> None:
        self._btn_traduci.setEnabled(self._ocr != "assente")
        self._btn_copia.setEnabled(bool(self._sel))

    # ---------- barra e avvisi ----------

    def _mostra_barra(self) -> None:
        larghezza = min(720, self.width() - 32)
        altezza = 56
        self._barra.setGeometry((self.width() - larghezza) // 2, self.height() - altezza - 40, larghezza, altezza)
        self._aggiorna_pulsanti()
        self._barra.show()
        self._barra.raise_()
        if self._ocr == "assente":
            self._mostra_avviso(MSG_OCR_ASSENTE)
        self.activateWindow()
        self._campo.setFocus()
        self.update()

    def _mostra_avviso(self, testo: str) -> None:
        self._avviso.setText(testo)
        self._avviso.adjustSize()
        base = self._barra.y() if self._barra.isVisible() else self.height() - 40
        self._avviso.move((self.width() - self._avviso.width()) // 2, base - self._avviso.height() - 12)
        self._avviso.show()
        self._avviso.raise_()

    def _invia(self, traduci: bool) -> None:
        if self._riquadro is None:
            return
        testo = gesti.testo_di(self._sel)
        messaggio = componi(self._campo.text(), testo, traduci)
        self.invia.emit(ritaglio_png(self._foto.immagine, self._riquadro), messaggio)

    def _copia(self) -> None:
        testo = gesti.testo_di(self._sel)
        if testo:
            self.copia.emit(testo)

    # ---------- disegno ----------

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(1 / self._dpr, 1 / self._dpr)  # da qui in poi: pixel fisici
        p.drawImage(0, 0, self._foto.immagine)
        w, h = self._limite.w, self._limite.h
        tutto = QPainterPath()
        tutto.addRect(0, 0, w, h)
        if self._riquadro is not None:
            raggio = 16 * self._dpr
            buco = QPainterPath()
            buco.addRoundedRect(_qrect(self._riquadro), raggio, raggio)
            p.fillPath(tutto.subtracted(buco), QColor(0, 0, 0, int(BUIO_FUORI * self._buio)))
        else:
            p.fillPath(tutto, QColor(0, 0, 0, int(BUIO_MAX * self._buio)))
        if self._luce > -0.5:
            self._disegna_luce(p, w, h)
        if self._tipo is TipoGesto.TESTO:
            for parola in self._sel:
                p.fillRect(_qrect(parola.rett), AZZURRO)
        if len(self._punti) > 1:
            self._disegna_tratto(p)
        if self._riquadro is not None:
            self._disegna_riquadro(p)
        p.end()

    def _disegna_luce(self, p: QPainter, w: float, h: float) -> None:
        centro = self._luce * (w + h)
        banda = 300 * self._dpr
        g = QLinearGradient(centro - banda, 0, centro, h)
        g.setColorAt(0.0, QColor(255, 255, 255, 0))
        g.setColorAt(0.5, QColor(255, 255, 255, 70))
        g.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(QRectF(0, 0, w, h), g)

    def _disegna_tratto(self, p: QPainter) -> None:
        percorso = QPainterPath(QPointF(*self._punti[0]))
        for q in self._punti[1:]:
            percorso.lineTo(QPointF(*q))
        for larghezza, alfa in ((22, 50), (12, 110), (5, 255)):
            penna = QPen(QColor(255, 255, 255, alfa), larghezza * self._dpr, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.strokePath(percorso, penna)

    def _disegna_riquadro(self, p: QPainter) -> None:
        raggio = 16 * self._dpr
        p.setPen(QPen(QColor(255, 255, 255), 3 * self._dpr))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(_qrect(self._riquadro), raggio, raggio)
        p.setBrush(QColor(255, 255, 255))
        r = self._riquadro
        for x, y in ((r.x, r.y), (r.destra, r.y), (r.x, r.basso), (r.destra, r.basso)):
            p.drawEllipse(QPointF(x, y), 7 * self._dpr, 7 * self._dpr)


class Sessione(QObject):
    """Uno strato per ogni schermo; una sola selezione alla volta."""

    invia = Signal(bytes, str)
    copia = Signal(str)
    chiusa = Signal()

    def __init__(self, foto: list[Foto], rett_elemento: Callable[[int, int, list[int]], Rett | None]) -> None:
        super().__init__()
        self._schermate: list[Schermata] = []
        self._chiusa = False

        def trova(x: int, y: int) -> Rett | None:
            return rett_elemento(x, y, [int(s.winId()) for s in self._schermate])

        for f in foto:
            s = Schermata(f, trova)
            s.gesto_iniziato.connect(lambda s=s: self._azzera_altre(s))
            s.invia.connect(self.invia)
            s.copia.connect(self.copia)
            s.esci.connect(self.chiudi)
            self._schermate.append(s)

    def mostra(self) -> None:
        schermo_mouse = QCursor.pos()
        for s in self._schermate:
            s.mostra(attiva=s.geometry().contains(schermo_mouse))

    def _azzera_altre(self, attiva: Schermata) -> None:
        for s in self._schermate:
            if s is not attiva:
                s.azzera()

    def chiudi(self) -> None:
        if self._chiusa:
            return
        self._chiusa = True
        for s in self._schermate:
            s.close()
            s.deleteLater()
        self._schermate.clear()
        self.chiusa.emit()
```

- [ ] **Step 3: Sostituire `cerchia\avvio.py`** (lo strato si apre; invio e copia per ora mostrano una notifica)

```python
"""Avvio di Cerchia e Chiedi: icona di notifica e collegamento dei pezzi."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from cerchia import cattura, elementi
from cerchia.schermata import Sessione
from cerchia.tasto_win import TastoWin

TITOLO = "Cerchia e Chiedi"


def _icona() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(217, 119, 87), 8))
    p.drawEllipse(10, 10, 44, 44)
    p.end()
    return QIcon(pix)


class Programma:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.sessione: Sessione | None = None
        self.icona = QSystemTrayIcon(_icona())
        self.icona.setToolTip(f"{TITOLO} — tieni premuto Win")
        self.menu = QMenu()
        esci = QAction("Esci", self.menu)
        esci.triggered.connect(app.quit)
        self.menu.addAction(esci)
        self.icona.setContextMenu(self.menu)
        self.icona.show()
        self.tasto = TastoWin()
        self.tasto.avvia.connect(self.apri)
        self.tasto.attiva()
        app.aboutToQuit.connect(self.tasto.disattiva)

    def avvisa(self, testo: str) -> None:
        self.icona.showMessage(TITOLO, testo)

    def apri(self) -> None:
        if self.sessione is not None:
            return
        try:
            s = Sessione(cattura.fotografa(), elementi.rett_elemento)
        except Exception as e:
            self.avvisa(f"Errore: {e}")
            return
        s.invia.connect(self._invia)
        s.copia.connect(self._copia)
        s.chiusa.connect(self._chiusa)
        self.sessione = s
        s.mostra()

    def _chiusa(self) -> None:
        self.sessione = None

    def _invia(self, png: bytes, messaggio: str) -> None:
        self.sessione.chiudi()
        self.avvisa(f"Da inviare ({len(png)} byte): {messaggio[:80]}")

    def _copia(self, testo: str) -> None:
        self.sessione.chiudi()
        self.avvisa(f"Da copiare: {testo[:80]}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    programma = Programma(app)  # noqa: F841 — tenuto vivo fino all'uscita
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Prova a mano dello strato**

Run: `.\.venv\Scripts\python -m cerchia.avvio`
Verificare con l'utente, tenendo premuto Win:
- lo schermo si congela, si scurisce e passa l'onda di luce;
- cerchio → riquadro arrotondato, resto più scuro, barra in basso con il cursore nella casella;
- angoli trascinabili;
- trascinamento su una riga di testo → parole azzurre, "Copia testo" attivo;
- clic su un pulsante o un'immagine → riquadro attorno all'elemento;
- Invio → notifica "Da inviare…" con il messaggio giusto;
- Esc → chiude tutto.

- [ ] **Step 5: Eseguire tutte le prove automatiche**

Run: `.\.venv\Scripts\python -m pytest -v`
Expected: 28 passed

---

### Task 9: Appunti e invio all'app di Claude

**Files:**
- Create: `cerchia\appunti.py`, `cerchia\invio_claude.py`
- Modify: `cerchia\avvio.py` — metodi `_invia` e `_copia` della classe `Programma`, più gli import

**Interfaces:**
- Consumes: `impostazioni` (Task 2), `tastiera.combinazione` (Task 6).
- Produces: `appunti.salva() -> QMimeData`, `appunti.ripristina(m: QMimeData)`, `appunti.metti_immagine(png: bytes)`, `appunti.metti_testo(t: str)`; `invio_claude.trova_finestra() -> int | None`; `invio_claude.invia(png: bytes, testo: str, avvisa: Callable[[str], None]) -> None`.

- [ ] **Step 1: Scrivere `cerchia\appunti.py`**

```python
"""Appunti di Windows: salvataggio, ripristino, immagine e testo."""
from PySide6.QtCore import QMimeData
from PySide6.QtGui import QGuiApplication, QImage


def salva() -> QMimeData:
    originale = QGuiApplication.clipboard().mimeData()
    copia = QMimeData()
    if originale is not None:
        for formato in originale.formats():
            copia.setData(formato, originale.data(formato))
    return copia


def ripristina(dati: QMimeData) -> None:
    QGuiApplication.clipboard().setMimeData(dati)


def metti_immagine(png: bytes) -> None:
    QGuiApplication.clipboard().setImage(QImage.fromData(png, "PNG"))


def metti_testo(testo: str) -> None:
    QGuiApplication.clipboard().setText(testo)
```

- [ ] **Step 2: Scrivere `cerchia\invio_claude.py`**

```python
"""Invio della selezione all'app desktop di Claude: chat nuova, incolla, invia."""
import ctypes
import os
import subprocess
import time
from collections.abc import Callable
from ctypes import wintypes

from PySide6.QtWidgets import QApplication

from cerchia import appunti, impostazioni, tastiera

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SW_RESTORE = 9
VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_V = 0x56

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [_ENUMPROC, wintypes.LPARAM]
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.BringWindowToTop.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                 ctypes.POINTER(wintypes.DWORD)]
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.GetCurrentThreadId.restype = wintypes.DWORD


def _aspetta(ms: int) -> None:
    fine = time.monotonic() + ms / 1000
    while time.monotonic() < fine:
        QApplication.processEvents()
        time.sleep(0.02)


def _percorso_processo(hwnd: int) -> str:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wintypes.DWORD(1024)
        if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return buf.value
        return ""
    finally:
        _kernel32.CloseHandle(h)


def trova_finestra() -> int | None:
    """Finestra principale dell'app desktop di Claude (esclude il claude.exe di Claude Code)."""
    trovate: list[int] = []

    @_ENUMPROC
    def cb(hwnd, _lparam):
        if _user32.IsWindowVisible(hwnd) and _user32.GetWindowTextLengthW(hwnd) > 0:
            percorso = _percorso_processo(hwnd).lower()
            if "\\anthropicclaude\\" in percorso and percorso.endswith("\\claude.exe"):
                trovate.append(hwnd)
                return False
        return True

    _user32.EnumWindows(cb, 0)
    return trovate[0] if trovate else None


def _attiva(hwnd: int) -> bool:
    if _user32.IsIconic(hwnd):
        _user32.ShowWindow(hwnd, SW_RESTORE)
    davanti = _user32.GetForegroundWindow()
    t_davanti = _user32.GetWindowThreadProcessId(davanti, None) if davanti else 0
    t_mio = _kernel32.GetCurrentThreadId()
    collegato = bool(t_davanti) and t_davanti != t_mio and bool(_user32.AttachThreadInput(t_mio, t_davanti, True))
    try:
        _user32.BringWindowToTop(hwnd)
        _user32.SetForegroundWindow(hwnd)
    finally:
        if collegato:
            _user32.AttachThreadInput(t_mio, t_davanti, False)
    for _ in range(20):
        if _user32.GetForegroundWindow() == hwnd:
            return True
        _aspetta(50)
    return False


def _apri_chat_nuova() -> bool:
    metodo, valore = impostazioni.CHAT_NUOVA
    if metodo == "tasti":
        tastiera.combinazione(*valore)
        return True
    if metodo == "link":
        os.startfile(valore)
        return True
    return False


def invia(png: bytes, testo: str, avvisa: Callable[[str], None]) -> None:
    salvati = appunti.salva()
    hwnd = trova_finestra()
    if hwnd is None:
        programma = os.path.expandvars(impostazioni.CLAUDE_EXE)
        if os.path.exists(programma):
            subprocess.Popen([programma])
        fine = time.monotonic() + 20
        while hwnd is None and time.monotonic() < fine:
            _aspetta(500)
            hwnd = trova_finestra()
        if hwnd is None:
            appunti.metti_immagine(png)
            avvisa("Claude non si è aperto: incolla con Ctrl+V.")
            return
        _aspetta(impostazioni.ATTESA_AVVIO_MS)

    if not _attiva(hwnd):
        appunti.metti_immagine(png)
        avvisa("Non riesco a portare Claude in primo piano: incolla con Ctrl+V.")
        return
    _aspetta(300)

    if _apri_chat_nuova():
        _aspetta(impostazioni.ATTESA_CHAT_NUOVA_MS)
    else:
        avvisa("Chat nuova non disponibile: uso la chat aperta.")

    appunti.metti_immagine(png)
    _aspetta(100)
    tastiera.combinazione(VK_CONTROL, VK_V)
    _aspetta(impostazioni.ATTESA_CARICAMENTO_MS)

    appunti.metti_testo(testo)
    _aspetta(100)
    tastiera.combinazione(VK_CONTROL, VK_V)
    _aspetta(200)
    tastiera.combinazione(VK_RETURN)

    _aspetta(300)
    appunti.ripristina(salvati)
```

- [ ] **Step 3: Collegare in `cerchia\avvio.py`**

Aggiungere agli import:

```python
from PySide6.QtCore import QTimer

from cerchia import appunti, invio_claude
```

Sostituire i metodi `_invia` e `_copia` della classe `Programma` con:

```python
    def _invia(self, png: bytes, messaggio: str) -> None:
        self.sessione.chiudi()
        QTimer.singleShot(80, lambda: invio_claude.invia(png, messaggio, self.avvisa))

    def _copia(self, testo: str) -> None:
        self.sessione.chiudi()
        appunti.metti_testo(testo)
        self.avvisa("Testo copiato.")
```

- [ ] **Step 4: Prova a mano dell'invio** (avvisare l'utente: l'app di Claude passerà a una chat nuova)

Run: `.\.venv\Scripts\python -m cerchia.avvio`
Verificare con l'utente:
- cerchio + domanda + Invio → chat nuova in Claude con immagine e domanda, risposta avviata;
- Traduci su un testo inglese → chat nuova con "Traduci in italiano questo testo: …";
- Copia testo → notifica "Testo copiato." e testo negli appunti;
- dopo l'invio gli appunti contengono di nuovo quello che c'era prima;
- con l'app di Claude chiusa → si apre e riceve la selezione.

Se l'immagine non fa in tempo a caricarsi, aumentare `ATTESA_CARICAMENTO_MS` in `impostazioni.py`.

- [ ] **Step 5: Eseguire tutte le prove automatiche**

Run: `.\.venv\Scripts\python -m pytest -v`
Expected: 28 passed

---

### Task 10: Avvio con Windows e lista delle prove a mano

**Files:**
- Create: `avvia.pyw`, `docs\prove-a-mano.md`
- Modify: `cerchia\avvio.py` — classe `Programma` (voce di menu) e nuove funzioni

**Interfaces:**
- Consumes: `Programma` (Task 8/9).
- Produces: `avvio.avvio_automatico_attivo() -> bool`, `avvio.imposta_avvio_automatico(attivo: bool) -> None`.

- [ ] **Step 1: Creare `avvia.pyw`**

```python
"""Avvia Cerchia e Chiedi senza finestra della console."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cerchia.avvio import main  # noqa: E402

main()
```

- [ ] **Step 2: Aggiungere in `cerchia\avvio.py`** (dopo le costanti) le funzioni del registro:

```python
import winreg
from pathlib import Path

CHIAVE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOME_RUN = "CerchiaEChiedi"


def _comando_avvio() -> str:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    script = Path(__file__).resolve().parent.parent / "avvia.pyw"
    return f'"{pythonw}" "{script}"'


def avvio_automatico_attivo() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHIAVE_RUN) as k:
            winreg.QueryValueEx(k, NOME_RUN)
            return True
    except FileNotFoundError:
        return False


def imposta_avvio_automatico(attivo: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHIAVE_RUN, 0, winreg.KEY_SET_VALUE) as k:
        if attivo:
            winreg.SetValueEx(k, NOME_RUN, 0, winreg.REG_SZ, _comando_avvio())
        else:
            try:
                winreg.DeleteValue(k, NOME_RUN)
            except FileNotFoundError:
                pass
```

e nel costruttore di `Programma`, prima di `self.menu.addAction(esci)`:

```python
        avvio_win = QAction("Avvia con Windows", self.menu)
        avvio_win.setCheckable(True)
        avvio_win.setChecked(avvio_automatico_attivo())
        avvio_win.toggled.connect(imposta_avvio_automatico)
        self.menu.addAction(avvio_win)
```

- [ ] **Step 3: Creare `docs\prove-a-mano.md`**

```markdown
# Prove a mano — Cerchia e Chiedi

Avvio: `.\.venv\Scripts\pythonw avvia.pyw` (oppure da "Avvia con Windows").

## Tasto Win
- [ ] Pressione breve di Win apre il menu Start.
- [ ] Win + E apre Esplora file; Win + Shift + S apre la cattura di Windows.
- [ ] Win tenuto premuto ~mezzo secondo apre lo strato; Start non si apre.

## Strato
- [ ] Schermo congelato, scurito, onda di luce.
- [ ] Cerchio → riquadro arrotondato, angoli trascinabili.
- [ ] Testo trascinato → parole azzurre; Copia testo attivo.
- [ ] Clic su un elemento → riquadro attorno all'elemento; clic sul desktop vuoto → "Nessun elemento qui, prova a cerchiare."
- [ ] Esc chiude senza inviare.
- [ ] Con due monitor a ridimensionamento diverso il ritaglio corrisponde al disegno.

## Invio
- [ ] Invio → chat nuova in Claude con immagine e domanda, risposta avviata.
- [ ] Casella vuota → "Cosa c'è in questa immagine? Spiegamelo."
- [ ] Traduci → "Traduci in italiano questo testo: …".
- [ ] Copia testo → "Testo copiato." e testo negli appunti.
- [ ] Appunti ripristinati dopo l'invio.
- [ ] App di Claude chiusa → si apre e riceve la selezione.

## Avvio con Windows
- [ ] Spunta "Avvia con Windows", riavvia il PC: l'icona compare da sola.
- [ ] Togli la spunta: dopo il riavvio non parte.

## Limiti noti
- Sopra programmi avviati come amministratore il tasto Win non viene intercettato.
- Win + L potrebbe non bloccare il PC mentre Win è in attesa del mezzo secondo.
```

- [ ] **Step 4: Prova a mano completa**

Run: `.\.venv\Scripts\pythonw avvia.pyw`
Percorrere con l'utente tutta `docs\prove-a-mano.md` e spuntare le voci.

- [ ] **Step 5: Eseguire tutte le prove automatiche**

Run: `.\.venv\Scripts\python -m pytest -v`
Expected: 28 passed
