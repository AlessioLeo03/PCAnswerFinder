# PCAnswerFinder

"Cerchia e cerca" di Android, ma su PC Windows e con Claude: tieni premuto **Win**, cerchia qualcosa sullo
schermo, scrivi una domanda e la selezione arriva all'app desktop di Claude.

## Installazione (per i colleghi)

1. Serve l'app desktop di Claude installata e con l'accesso fatto: https://claude.ai/download
2. Avvia `PCAnswerFinder-Setup-<versione>.exe`.
   - Non servono permessi di amministratore: il programma va in `%LOCALAPPDATA%\Programs\PCAnswerFinder`.
   - Se Windows mostra "Windows ha protetto il PC", clicca **Ulteriori informazioni** e poi **Esegui comunque**
     (l'installatore non è firmato digitalmente).
3. Lascia la spunta su "Avvia PCAnswerFinder insieme a Windows" e completa l'installazione.
4. Vicino all'orologio compare un cerchio arancione: il programma è attivo.

Disinstallazione: Impostazioni > App > App installate > PCAnswerFinder > Disinstalla.

## Uso

- **Win tenuto premuto ~mezzo secondo**: lo schermo si ferma e compare il suggerimento.
- **Cerchia / scarabocchia** una zona, **trascina** su un testo per evidenziarlo, oppure **clicca** su un elemento.
- Nella barra in basso: scrivi la domanda e premi **Invio** (o la freccia arancione).
  - **Traduci**: traduzione in italiano del testo nell'immagine.
  - **Copia testo**: copia negli appunti il testo riconosciuto.
  - Menu accanto alla freccia: **Chat nuova**, **Chat aperta** oppure **Cerca chat…** con l'elenco delle chat
    presenti nella barra laterale dell'app di Claude.
- **Esc** chiude senza inviare. Una pressione breve di Win apre Start come sempre.

Gli errori vengono scritti in `%LOCALAPPDATA%\PCAnswerFinder\errori.log`.

## Sviluppo

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install PySide6 uiautomation winrt-runtime winrt-Windows.Media.Ocr winrt-Windows.Graphics.Imaging winrt-Windows.Storage.Streams winrt-Windows.Foundation winrt-Windows.Foundation.Collections winrt-Windows.Globalization pytest pyinstaller
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\pythonw avvia.pyw
```

### Creare l'installatore

Serve Inno Setup 6 (`winget install JRSoftware.InnoSetup --source winget --scope user`).

```powershell
.\pacchetto\costruisci.ps1 -Versione 1.0.0
```

Il risultato è `dist\PCAnswerFinder-Setup-1.0.0.exe` (prove automatiche, PyInstaller, Inno Setup).
Documentazione: [specifica](docs/specifica.md), [prove a mano](docs/prove-a-mano.md).
