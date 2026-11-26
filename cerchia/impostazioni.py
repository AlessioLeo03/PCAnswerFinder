"""Costanti regolabili di PCAnswerFinder."""

# Programma che apre l'app desktop di Claude
CLAUDE_EXE = r"%LOCALAPPDATA%\AnthropicClaude\claude.exe"
# Se manca l'installer classico, avvio della versione del Microsoft Store
CLAUDE_STORE_APPID = r"shell:AppsFolder\Claude_pzs8sxrjxfjjc!Claude"

# Come aprire una chat nuova nell'app di Claude (deciso nel Task 2 del piano):
#   ("tasti", [codici VK in ordine di pressione])
#   ("link", "indirizzo claude://...")
#   ("nessuno", None)  -> si usa la chat aperta
VK_CONTROL = 0x11
CHAT_NUOVA: tuple[str, object] = ("tasti", [VK_CONTROL, ord("N")])

# Ricerca di una chat per titolo nell'app di Claude (verificato dall'utente: Ctrl+K, titolo, Invio)
CERCA_CHAT = [VK_CONTROL, ord("K")]

# Attese in millisecondi
ATTESA_AVVIO_MS = 2500        # dopo l'apertura dell'app
ATTESA_CHAT_NUOVA_MS = 800    # dopo il comando "chat nuova"
ATTESA_CARICAMENTO_MS = 1500  # dopo aver incollato l'immagine
ATTESA_RICERCA_MS = 600       # dopo Ctrl+K, prima di scrivere il titolo
ATTESA_RISULTATI_MS = 800     # dopo il titolo, prima di Invio
