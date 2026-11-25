"""Composizione del testo da mandare a Claude insieme all'immagine.

Come su Android, a Claude arriva solo l'immagine con la domanda: il testo
letto dall'OCR serve per evidenziare e per "Copia testo", non viene incollato.
"""

DOMANDA_VUOTA = "Cosa c'è in questa immagine? Spiegamelo."
TRADUCI_IMMAGINE = "Traduci in italiano il testo che vedi nell'immagine."


def componi(domanda: str, traduci: bool = False) -> str:
    if traduci:
        return TRADUCI_IMMAGINE
    return domanda.strip() or DOMANDA_VUOTA
