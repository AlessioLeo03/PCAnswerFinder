"""Costanti regolabili di Cerchia e Chiedi."""

# Programma che apre l'app desktop di Claude
CLAUDE_EXE = r"%LOCALAPPDATA%\AnthropicClaude\claude.exe"

# Come aprire una chat nuova nell'app di Claude (deciso nel Task 2 del piano):
#   ("tasti", [codici VK in ordine di pressione])
#   ("link", "indirizzo claude://...")
#   ("nessuno", None)  -> si usa la chat aperta
VK_CONTROL = 0x11
CHAT_NUOVA: tuple[str, object] = ("tasti", [VK_CONTROL, ord("N")])

# Attese in millisecondi
ATTESA_AVVIO_MS = 2500        # dopo l'apertura dell'app
ATTESA_CHAT_NUOVA_MS = 800    # dopo il comando "chat nuova"
ATTESA_CARICAMENTO_MS = 1500  # dopo aver incollato l'immagine
