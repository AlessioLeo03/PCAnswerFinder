from PySide6.QtCore import QSettings

from cerchia import destinazione
from cerchia.destinazione import APERTA, CERCA, NUOVA, Destinazione


def _qs(tmp_path):
    return QSettings(str(tmp_path / "prova.ini"), QSettings.IniFormat)


def test_predefinita_chat_nuova(tmp_path):
    assert destinazione.carica(_qs(tmp_path)) == Destinazione(NUOVA, "")


def test_salva_e_ricarica(tmp_path):
    destinazione.salva(Destinazione(CERCA, "PCAnswerFinder"), _qs(tmp_path))
    assert destinazione.carica(_qs(tmp_path)) == Destinazione(CERCA, "PCAnswerFinder")


def test_modo_sconosciuto_torna_chat_nuova(tmp_path):
    qs = _qs(tmp_path)
    qs.setValue("destinazione/modo", "boh")
    assert destinazione.carica(qs).modo == NUOVA


def test_cerca_senza_titolo_non_valida():
    assert not Destinazione(CERCA, "  ").valida()
    assert Destinazione(CERCA, "x").valida()
    assert Destinazione(APERTA).valida()
    assert Destinazione(NUOVA).valida()
