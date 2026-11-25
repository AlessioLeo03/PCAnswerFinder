import pytest
from PySide6.QtWidgets import QApplication

from cerchia import appunti, invio_claude, tastiera
from cerchia.destinazione import APERTA, CERCA, NUOVA, Destinazione


@pytest.fixture(scope="module", autouse=True)
def proteggi_appunti(app):
    originali = appunti.salva()
    yield
    appunti.ripristina(originali)


def test_appunti_ripristinati_se_eccezione(app, monkeypatch):
    def guasta(_hwnd):
        raise RuntimeError("x")

    monkeypatch.setattr(invio_claude, "trova_finestra", lambda: 123)
    monkeypatch.setattr(invio_claude, "_attiva", guasta)
    appunti.metti_testo("originale")
    messaggi = []
    invio_claude.invia(b"png", "t", messaggi.append)
    assert QApplication.clipboard().text() == "originale"
    assert messaggi and messaggi[0].startswith("Errore durante l'invio:")


CTRL = invio_claude.VK_CONTROL
INCOLLA = (CTRL, invio_claude.VK_V)
INVIO = (invio_claude.VK_RETURN,)


def _registra(monkeypatch):
    """Finge l'app di Claude e annota tasti e testi messi negli appunti."""
    eventi = []
    monkeypatch.setattr(invio_claude, "trova_finestra", lambda: 123)
    monkeypatch.setattr(invio_claude, "_attiva", lambda _h: True)
    monkeypatch.setattr(invio_claude, "_aspetta", lambda _ms: None)
    monkeypatch.setattr(tastiera, "combinazione", lambda *vks: eventi.append(("tasti", vks)))
    originale = appunti.metti_testo

    def metti_testo(t):
        eventi.append(("testo", t))
        originale(t)

    monkeypatch.setattr(appunti, "metti_testo", metti_testo)
    monkeypatch.setattr(appunti, "metti_immagine", lambda _png: eventi.append(("immagine",)))
    return eventi


def test_chat_nuova_preme_ctrl_n(app, monkeypatch):
    eventi = _registra(monkeypatch)
    invio_claude.invia(b"png", "domanda", lambda _m: None, Destinazione(NUOVA))
    assert eventi == [("tasti", (CTRL, ord("N"))), ("immagine",), ("tasti", INCOLLA),
                      ("testo", "domanda"), ("tasti", INCOLLA), ("tasti", INVIO)]


def test_chat_aperta_non_cambia_chat(app, monkeypatch):
    eventi = _registra(monkeypatch)
    invio_claude.invia(b"png", "domanda", lambda _m: None, Destinazione(APERTA))
    assert eventi == [("immagine",), ("tasti", INCOLLA), ("testo", "domanda"), ("tasti", INCOLLA), ("tasti", INVIO)]


def test_cerca_chat_usa_ctrl_k_e_titolo(app, monkeypatch):
    eventi = _registra(monkeypatch)
    invio_claude.invia(b"png", "domanda", lambda _m: None, Destinazione(CERCA, "  PCAnswerFinder "))
    assert eventi == [("tasti", (CTRL, ord("K"))), ("testo", "PCAnswerFinder"), ("tasti", INCOLLA),
                      ("tasti", INVIO), ("immagine",), ("tasti", INCOLLA), ("testo", "domanda"),
                      ("tasti", INCOLLA), ("tasti", INVIO)]
