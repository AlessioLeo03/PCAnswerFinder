import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from cerchia import scorciatoia
from cerchia.finestra_scorciatoia import IN_ASCOLTO, MSG_NON_VALIDA, FinestraScorciatoia
from cerchia.scorciatoia import PREDEFINITA, Scorciatoia

Q, F9 = ord("Q"), 0x78


_aperte = []


@pytest.fixture(autouse=True)
def chiudi_finestre(app):
    yield
    while _aperte:
        f = _aperte.pop()
        f.close()
        f.deleteLater()
    QApplication.processEvents()


def _finestra(t, attuale=PREDEFINITA):
    f = FinestraScorciatoia(t, attuale)
    _aperte.append(f)
    return f


class TastoFinto(QObject):
    registrata = Signal(object)

    def __init__(self):
        super().__init__()
        self.in_registrazione = False
        self.fermate = 0

    def registra(self):
        self.in_registrazione = True

    def ferma_registrazione(self, risultato=None):
        self.in_registrazione = False
        self.fermate += 1
        self.registrata.emit(risultato)


def test_registra_e_salva_una_combinazione(app):
    t = TastoFinto()
    f = _finestra(t)
    assert f.btn_registra.text() == "Tieni premuto Win"
    assert not f._riga_soglia.isHidden()
    f.btn_registra.click()
    assert t.in_registrazione and f.btn_registra.text() == IN_ASCOLTO
    assert not f.btn_salva.isEnabled()
    nuova = Scorciatoia(Q, frozenset({"ctrl", "maiusc"}))
    t.ferma_registrazione(nuova)
    assert f.btn_registra.text() == "Ctrl + Maiusc + Q"
    assert f._riga_soglia.isHidden() and f.btn_salva.isEnabled()
    salvate = []
    f.scelta.connect(salvate.append)
    f.btn_salva.click()
    assert salvate == [nuova]
    assert scorciatoia.carica() == nuova


def test_tasto_singolo_usa_la_soglia_scelta(app):
    t = TastoFinto()
    f = _finestra(t)
    f.soglia.setValue(8)
    assert f.etichetta_soglia.text() == "Tempo da tenere premuto: 0,8 s"
    f.btn_registra.click()
    t.ferma_registrazione(Scorciatoia(F9, lunga=True))
    assert f._scelta == Scorciatoia(F9, lunga=True, soglia_ms=800)
    assert f.btn_registra.text() == "Tieni premuto F9"
    f.reject()


def test_tasti_non_validi_mostrano_spiegazione(app):
    t = TastoFinto()
    f = _finestra(t)
    f.btn_registra.click()
    t.ferma_registrazione(None)
    assert f.avviso.text() == MSG_NON_VALIDA and not f.avviso.isHidden()
    assert f._scelta == PREDEFINITA
    f.reject()


def test_chiudere_ferma_la_registrazione(app):
    t = TastoFinto()
    f = _finestra(t)
    f.btn_registra.click()
    f.reject()
    assert not t.in_registrazione and t.fermate == 1
