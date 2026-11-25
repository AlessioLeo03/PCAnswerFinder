"""Appunti di Windows: salvataggio, ripristino, immagine e testo."""
from PySide6.QtCore import QMimeData
from PySide6.QtGui import QGuiApplication, QImage


def salva() -> QMimeData:
    originale = QGuiApplication.clipboard().mimeData()
    copia = QMimeData()
    if originale is not None:
        for formato in originale.formats():
            copia.setData(formato, originale.data(formato))
    return copia


def ripristina(dati: QMimeData) -> None:
    QGuiApplication.clipboard().setMimeData(dati)


def metti_immagine(png: bytes) -> None:
    QGuiApplication.clipboard().setImage(QImage.fromData(png, "PNG"))


def metti_testo(testo: str) -> None:
    QGuiApplication.clipboard().setText(testo)
