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
