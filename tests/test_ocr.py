import threading

import pytest
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter

from cerchia import ocr
from cerchia.cattura import png_da_immagine


@pytest.fixture(scope="module")
def app():
    return QGuiApplication.instance() or QGuiApplication([])


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
