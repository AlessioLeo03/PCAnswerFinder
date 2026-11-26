# PCAnswerFinder — Specifica

Data: 25 novembre 2026
Stato: in revisione

## 1. Obiettivo

Portare su PC Windows l'esperienza di "Cerchia e cerca" dei telefoni Android, ma con Claude al posto di
Google. L'utente tiene premuto il tasto Win, lo schermo si congela, seleziona qualcosa con il mouse (cerchio,
scarabocchio, testo evidenziato o clic su un elemento), scrive una domanda e la selezione arriva in una chat
nuova dell'app desktop di Claude, già inviata.

### Fuori ambito (prima versione)

- Risposta dentro il riquadro sopra lo schermo (richiederebbe la chiave API; scelta scartata).
- Riconoscimento di musica, ricerca per prodotti, cronologia delle selezioni.
- macOS e Linux.

## 2. Requisiti

| # | Requisito |
|---|-----------|
| R1 | Tenere premuto Win per almeno 500 ms avvia la cattura. |
| R2 | Una pressione di Win più breve di 500 ms apre il menu Start come al solito. |
| R3 | Win usato insieme a un altro tasto (Win+E, Win+D, …) funziona come al solito. |
| R4 | All'avvio vengono fotografati tutti gli schermi; lo strato mostra la foto congelata, scurita, con un'onda di luce. |
| R5 | Gesto "cerchio/scarabocchio": tratto luminoso a mano libera; al rilascio diventa un riquadro arrotondato attorno alla zona, ridimensionabile dagli angoli. |
| R6 | Gesto "evidenzia testo": trascinamento che parte su una parola riconosciuta dall'OCR; le parole toccate si colorano di azzurro. |
| R7 | Gesto "clic": clic fermo seleziona l'elemento dell'interfaccia sotto il mouse (finestra, immagine, blocco di testo). |
| R8 | Un nuovo gesto sostituisce la selezione precedente. |
| R9 | Barra in basso con casella "Chiedi a Claude su questa selezione…" e pulsanti Traduci e Copia testo. Invio invia; Esc chiude senza inviare. |
| R10 | Copia testo è attivo solo se la selezione contiene testo riconosciuto; copia negli appunti e chiude, senza coinvolgere Claude. |
| R11 | L'invio apre una chat nuova nell'app desktop di Claude, incolla immagine e testo e invia automaticamente. |
| R12 | Dopo l'invio gli appunti tornano come erano prima. |
| R13 | Le foto dello schermo restano solo in memoria; mai salvate su disco. |
| R14 | Icona nell'area di notifica con le voci "Avvia con Windows" (attiva/disattiva) ed "Esci". |

## 3. Tecnologia

- Python 3.12 (già installato), ambiente virtuale in `cerchia-e-chiedi\.venv`.
- `PySide6`: interfaccia, strato a tutto schermo, disegno, animazioni, icona di notifica, cattura schermi
  (`QScreen.grabWindow`).
- `winrt-Windows.Media.Ocr` e pacchetti winrt collegati: OCR incluso in Windows.
- `uiautomation`: elemento sotto il mouse tramite UI Automation.
- `ctypes` (libreria standard): hook di tastiera a basso livello, `SendInput`, appunti, attivazione finestre.
- `pytest`: prove automatiche.

Il programma dichiara la consapevolezza DPI per singolo monitor (Per-Monitor V2), così coordinate e ritagli
sono corretti con più schermi e con ridimensionamento 125 % / 150 %.

## 4. Struttura

Un file per compito, in `cerchia-e-chiedi\cerchia\`:

| File | Compito | Dipende da |
|------|---------|------------|
| `avvio.py` | Avvia l'applicazione Qt, crea l'icona di notifica, collega gli altri pezzi. | tutti |
| `tasto_win.py` | Hook `WH_KEYBOARD_LL`. Macchina a stati della pressione di Win (vedi §5). Emette il segnale "avvia". | ctypes |
| `stato_win.py` | Macchina a stati pura (senza Windows): riceve eventi e tempi, decide cosa fare. Provabile da sola. | nulla |
| `cattura.py` | Foto di tutti gli schermi con la loro geometria in pixel fisici. | PySide6 |
| `schermata.py` | Strato a tutto schermo per ogni monitor: foto, oscuramento, onda di luce, tratto, riquadro, barra. | PySide6, gesti, ocr, elementi |
| `gesti.py` | Logica pura: classifica il gesto, calcola il riquadro dal tratto, sceglie le parole evidenziate. | nulla |
| `ocr.py` | Esegue l'OCR in un thread separato; restituisce parole con il loro rettangolo. | winrt |
| `elementi.py` | Rettangolo dell'elemento UI Automation sotto un punto. | uiautomation |
| `messaggio.py` | Logica pura: compone il testo da mandare a Claude (vedi §6). | nulla |
| `invio_claude.py` | Porta in primo piano l'app di Claude, apre una chat nuova, incolla, invia, ripristina gli appunti. | ctypes |
| `appunti.py` | Salva e ripristina gli appunti; mette un'immagine o un testo negli appunti. | ctypes / PySide6 |

## 5. Tasto Win

Macchina a stati in `stato_win.py`:

- **Riposo** → Win premuto: il programma blocca l'evento e passa a **Attesa**, annotando l'ora.
- **Attesa** → passano 500 ms con Win ancora premuto: passa a **Avviato** ed emette "avvia".
- **Attesa** → Win rilasciato prima di 500 ms: reinvia Win giù + Win su con `SendInput` (il menu Start si
  apre), torna a **Riposo**.
- **Attesa** → un altro tasto premuto: reinvia Win giù, lascia passare l'altro tasto, passa a
  **Combinazione**; al rilascio di Win lascia passare il rilascio e torna a **Riposo**.
- **Avviato** → Win rilasciato: blocca anche il rilascio (Windows non ha mai visto la pressione, quindi il
  menu Start non si apre); torna a **Riposo**.
- **Avviato** → altri tasti premuti mentre Win è ancora giù: lasciati passare senza Win.

Gli eventi reinviati dal programma portano un valore riconoscibile in `dwExtraInfo` e l'hook li ignora.
Il controllo dei 500 ms usa un timer Qt; l'hook resta veloce (nessun lavoro pesante dentro la callback).

### Scorciatoia personalizzata (versione 1.1)

Dal menu dell'icona, "Scorciatoia…" apre una finestra che registra i tasti premuti con lo stesso hook
(durante la registrazione nessun tasto arriva alle altre app). Modificatori + un tasto normale = combinazione
esatta (`StatoCombinazione`: il tasto normale viene bloccato; con Win o Alt si invia il tasto senza funzione
0xE8 per non aprire Start o i menu). Un solo tasto = "tieni premuto" con soglia 0,2–1,5 s (`StatoWin`
generalizzato). Combinazioni d'uso comune (Ctrl+C, Alt+F4, una lettera tenuta premuta…) chiedono conferma.
Salvata in QSettings; predefinita: tieni premuto Win per 0,5 s.

## 6. Gesti, selezione e messaggio

### Classificazione del gesto (`gesti.py`)

- Spostamento totale < 6 px tra pressione e rilascio → **clic**.
- Pressione sopra il rettangolo di una parola OCR e tratto con altezza < 1,5 × altezza della riga → **testo**.
- Altrimenti → **cerchio/scarabocchio**.

### Riquadro dal tratto

Rettangolo che contiene tutti i punti del tratto, allargato di 12 px per lato e limitato ai bordi dello
schermo. Dimensione minima 32 × 32 px.

### Parole evidenziate

Tutte le parole OCR, in ordine di lettura, comprese tra la parola sotto il punto di partenza e quella sotto
il punto di arrivo (come una selezione di testo normale). Il riquadro dell'immagine è l'unione dei loro
rettangoli, allargato di 8 px.

### Testo della selezione

Per cerchio e clic: le parole OCR il cui centro cade dentro il riquadro. Per testo: le parole evidenziate.

### Messaggio (`messaggio.py`)

| Situazione | Testo inviato insieme all'immagine |
|------------|-------------------------------------|
| Domanda scritta | la domanda |
| Casella vuota | `Cosa c'è in questa immagine? Spiegamelo.` |
| Pulsante Traduci | `Traduci in italiano il testo che vedi nell'immagine.` |

Come su Android, il testo letto dall'OCR non viene incollato nel messaggio (decisione dell'utente,
25 novembre 2026): serve solo per evidenziare le parole e per "Copia testo".

L'immagine inviata è sempre il ritaglio del riquadro dalla foto congelata, in PNG, alla risoluzione fisica.

## 7. Invio all'app di Claude

1. Salva il contenuto attuale degli appunti.
2. Chiude lo strato.
3. Trova la finestra dell'app desktop (`claude.exe` con percorso dentro `\AnthropicClaude\`, titolo non
   vuoto). Se non c'è, avvia `%LOCALAPPDATA%\AnthropicClaude\claude.exe` e aspetta fino a 20 s.
4. Porta la finestra in primo piano.
5. Va sulla chat scelta nel menu della barra (la scelta e l'ultimo titolo vengono ricordati):
   - **Chat nuova**: `Ctrl+N` (verificato dall'utente). Se non disponibile: chat aperta + notifica.
   - **Chat aperta**: nessun tasto, usa la chat aperta in quel momento.
   - **Cerca chat…**: `Ctrl+K`, incolla il titolo scritto nella casella "Titolo chat", attesa dei risultati
     (0,8 s), `Invio` (verificato dall'utente). Titolo vuoto: lo strato resta aperto con
     "Scrivi il titolo della chat". Se nessuna chat corrisponde il risultato non è controllabile.
     Il menu propone le chat più attinenti a quanto scritto: quelle già cercate (ultime 20) e quelle visibili
     nella barra laterale dell'app, lette con UI Automation dai pulsanti "Altre opzioni per <titolo>"
     (`chat_claude.py`, in un thread a parte all'avvio e a ogni apertura dello strato, circa 0,6 s).
6. Mette l'immagine negli appunti, `Ctrl+V`, attesa del caricamento (tempo fisso configurabile, partenza
   1,5 s).
7. Mette il testo negli appunti, `Ctrl+V`, `Invio`.
8. Ripristina gli appunti salvati.

## 8. Errori

| Caso | Comportamento |
|------|---------------|
| App di Claude non si apre in 20 s | Immagine negli appunti, notifica "Claude non si è aperto: incolla con Ctrl+V". |
| Chat nuova non apribile | Incolla nella chat corrente, notifica. |
| OCR non disponibile (manca la lingua) | Evidenzia testo e Copia testo disattivati; cerchio e clic funzionano; messaggio nella barra. |
| Clic senza elemento | Lo strato resta aperto, messaggio "Nessun elemento qui, prova a cerchiare". |
| Programma bloccato o chiuso | Windows rimuove l'hook: Win torna normale. |
| Finestra in primo piano avviata come amministratore | L'hook non riceve Win: limite noto, documentato. |
| Errore imprevisto nello strato | Lo strato si chiude, notifica con il messaggio, il programma resta attivo. |

## 9. Ordine di lavoro

1. **Verifica preliminare:** trovare come aprire una chat nuova nell'app desktop di Claude in modo affidabile.
   Il risultato decide il §7 punto 5.
2. Logica pura con prove: `stato_win.py`, `gesti.py`, `messaggio.py`.
3. `tasto_win.py` + icona di notifica.
4. `cattura.py` + `schermata.py` (solo cerchio).
5. `ocr.py` + evidenzia testo + Copia testo + Traduci.
6. `elementi.py` + clic.
7. `invio_claude.py` + `appunti.py`.
8. "Avvia con Windows" (voce `PCAnswerFinder` in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

## 10. Prove

### Automatiche (`pytest`, cartella `tests\`)

- `stato_win`: pressione breve → Start reinviato; pressione lunga → "avvia" e rilascio bloccato; Win+E → combinazione
  lasciata passare; eventi reinviati ignorati.
- `gesti`: classificazione clic / testo / cerchio; riquadro con margine, bordi e dimensione minima; selezione delle
  parole tra inizio e fine su più righe.
- `messaggio`: tutte le righe della tabella del §6.

### A mano (lista di controllo in `docs\prove-a-mano.md`)

- Pressione breve di Win apre Start; Win+E apre Esplora file; pressione lunga apre lo strato.
- Cerchio, testo e clic su due monitor con ridimensionamento diverso: il ritaglio corrisponde al disegno.
- Copia testo copia il testo giusto.
- Invio: chat nuova, immagine e testo presenti, risposta di Claude avviata, appunti ripristinati.
- App di Claude chiusa: si apre e riceve la selezione.
