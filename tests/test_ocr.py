import threading

from PySide6.QtGui import QColor, QFont, QImage, QPainter

from cerchia import ocr
from cerchia.cattura import png_da_immagine


def test_legge_parole_con_posizione(app):
    img = QImage(700, 140, QImage.Format_RGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    font = QFont("Segoe UI")
    font.setPixelSize(56)
    p.setFont(font)
    p.setPen(QColor("black"))
    p.drawText(20, 95, "Ciao mondo")
    p.end()
    png = png_da_immagine(img)

    risultato = {}
    t = threading.Thread(target=lambda: risultato.update(parole=ocr.leggi(png)))
    t.start()
    t.join(30)

    parole = risultato["parole"]
    assert parole is not None, "OCR di Windows non disponibile"
    assert [x.testo for x in parole] == ["Ciao", "mondo"]
    assert all(x.riga == 0 for x in parole)
    assert parole[0].rett.x < parole[1].rett.x


def test_avvia_codifica_png_fuori_dal_thread_chiamante(app, monkeypatch):
    import time
    from PySide6.QtCore import QObject

    chiamate = []

    def finto(img):
        chiamate.append(threading.current_thread())
        return b""

    monkeypatch.setattr(ocr, "png_da_immagine", finto)
    monkeypatch.setattr(ocr, "leggi", lambda png: [])
    ricevuto = []

    class Ricevitore(QObject):
        def prendi(self, parole):
            ricevuto.append(parole)

    lettore = ocr.LettoreOcr()
    r = Ricevitore()
    lettore.pronto.connect(r.prendi)
    lettore.avvia(QImage(10, 10, QImage.Format_RGB32))
    fine = time.monotonic() + 30
    while not ricevuto and time.monotonic() < fine:
        app.processEvents()
        time.sleep(0.01)
    assert ricevuto == [[]]
    assert chiamate and all(t is not threading.main_thread() for t in chiamate)
