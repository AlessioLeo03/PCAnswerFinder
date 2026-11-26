"""Appunti di Windows: salvataggio, ripristino, immagine e testo."""
import time

from PySide6.QtCore import QMimeData
from PySide6.QtGui import QGuiApplication, QImage


def salva() -> QMimeData:
    originale = QGuiApplication.clipboard().mimeData()
    copia = QMimeData()
    if originale is not None:
        for formato in originale.formats():
            copia.setData(formato, originale.data(formato))
    return copia


def ripristina(dati: QMimeData, tentativi: int = 10) -> None:
    """Rimette negli appunti i dati salvati.

    Gli appunti di Windows sono condivisi: se un altro programma li tiene aperti in quel momento
    (cronologia degli appunti, gestori di appunti…) la scrittura può non riuscire. Si riprova un po'.
    """
    formati = dati.formats()
    for _ in range(tentativi):
        copia = QMimeData()  # Qt prende possesso dell'oggetto: ogni tentativo ne usa uno nuovo
        for formato in formati:
            copia.setData(formato, dati.data(formato))
        QGuiApplication.clipboard().setMimeData(copia)
        attuali = QGuiApplication.clipboard().mimeData()
        if not formati or (attuali is not None and attuali.formats()):
            return
        time.sleep(0.05)


def metti_immagine(png: bytes) -> None:
    QGuiApplication.clipboard().setImage(QImage.fromData(png, "PNG"))


def metti_testo(testo: str) -> None:
    QGuiApplication.clipboard().setText(testo)
