import pytest
from PySide6.QtWidgets import QApplication

from cerchia import appunti, invio_claude


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
