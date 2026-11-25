import pytest
from PySide6.QtGui import QColor, QImage

from cerchia.cattura import ritaglio_png
from cerchia.gesti import Rett


def _dimensioni(app, r):
    img = QImage(100, 100, QImage.Format_RGB32)
    img.fill(QColor("white"))
    out = QImage.fromData(ritaglio_png(img, r), "PNG")
    return out.width(), out.height()


def test_bordi_esatti(app):
    assert _dimensioni(app, Rett(10.5, 10.5, 10.5, 10.5)) == (11, 11)


def test_limitato_all_immagine(app):
    assert _dimensioni(app, Rett(90, 90, 30, 30)) == (10, 10)


@pytest.mark.parametrize("r", [Rett(10, 10, 0, 0), Rett(200, 200, 10, 10)])
def test_ritaglio_vuoto_non_restituisce_immagine(app, r):
    img = QImage(100, 100, QImage.Format_RGB32)
    img.fill(QColor("white"))
    assert ritaglio_png(img, r) == b""
