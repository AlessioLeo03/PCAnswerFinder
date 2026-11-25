from cerchia import avvio
from cerchia.avvio import Programma
from cerchia.destinazione import Destinazione


def test_apri_ignorato_durante_invio(monkeypatch):
    chiamate = []
    monkeypatch.setattr(avvio.cattura, "fotografa", lambda: chiamate.append(1))
    p = Programma.__new__(Programma)
    p.sessione = None
    p._invio_in_corso = True
    p.apri()
    assert chiamate == []


def test_invia_ignorato_durante_invio(monkeypatch):
    chiamate = []
    monkeypatch.setattr(avvio.invio_claude, "invia", lambda *a: chiamate.append(a))
    p = Programma.__new__(Programma)
    p.sessione = None
    p._invio_in_corso = True
    p._invia(b"png", "m", Destinazione())
    assert chiamate == []
