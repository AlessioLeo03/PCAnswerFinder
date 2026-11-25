import pytest
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from cerchia import appunti


@pytest.fixture(scope="module", autouse=True)
def proteggi_appunti(app):
    originali = appunti.salva()
    yield
    appunti.ripristina(originali)


def test_metti_testo(app):
    appunti.metti_testo("ciao")
    assert QApplication.clipboard().text() == "ciao"


def test_salva_e_ripristina(app):
    appunti.metti_testo("prima")
    salvati = appunti.salva()
    appunti.metti_testo("dopo")
    appunti.ripristina(salvati)
    assert QApplication.clipboard().text() == "prima"


def test_metti_immagine(app):
    img = QImage(20, 10, QImage.Format_RGB32)
    img.fill(QColor(10, 20, 30))
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    appunti.metti_immagine(bytes(buf.data()))
    letta = QApplication.clipboard().image()
    assert (letta.width(), letta.height()) == (20, 10)
