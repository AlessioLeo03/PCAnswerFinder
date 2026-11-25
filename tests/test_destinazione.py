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


def test_cerca_salva_i_titoli_recenti(tmp_path):
    qs = _qs(tmp_path)
    destinazione.salva(Destinazione(CERCA, "Uno"), qs)
    assert destinazione.recenti(qs) == ["Uno"]
    destinazione.salva(Destinazione(CERCA, "Due"), qs)
    destinazione.salva(Destinazione(CERCA, "uno"), qs)
    destinazione.salva(Destinazione(NUOVA, ""), qs)
    assert destinazione.recenti(_qs(tmp_path)) == ["uno", "Due"]


def test_recenti_al_massimo_venti():
    elenco = []
    for i in range(25):
        elenco = destinazione.aggiungi_recente(elenco, f"chat {i}")
    assert len(elenco) == destinazione.MAX_RECENTI == 20
    assert elenco[0] == "chat 24"


def test_suggerimenti_piu_attinenti_prima():
    elenco = ["Ricette di casa", "Progetto PCAnswerFinder", "PC nuovo", "Spesa", "Appunti PC"]
    assert destinazione.suggerimenti(elenco, "pc") == ["PC nuovo", "Progetto PCAnswerFinder", "Appunti PC"]
    assert destinazione.suggerimenti(elenco, "  ") == elenco
    assert destinazione.suggerimenti(elenco, "zzz") == []
    assert destinazione.suggerimenti(elenco, "es", quanti=1) == ["Spesa"]


def test_cerca_senza_titolo_non_valida():
    assert not Destinazione(CERCA, "  ").valida()
    assert Destinazione(CERCA, "x").valida()
    assert Destinazione(APERTA).valida()
    assert Destinazione(NUOVA).valida()
