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
