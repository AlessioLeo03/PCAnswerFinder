from cerchia.messaggio import DOMANDA_VUOTA, TRADUCI_IMMAGINE, componi


def test_domanda_scritta():
    assert componi("Che cos'è?") == "Che cos'è?"


def test_domanda_senza_spazi_ai_bordi():
    assert componi("  Spiega  ") == "Spiega"


def test_casella_vuota():
    assert componi("   ") == DOMANDA_VUOTA
    assert DOMANDA_VUOTA == "Cosa c'è in questa immagine? Spiegamelo."


def test_traduci_ignora_la_domanda():
    assert componi("ignorata", traduci=True) == TRADUCI_IMMAGINE
    assert TRADUCI_IMMAGINE == "Traduci in italiano il testo che vedi nell'immagine."
