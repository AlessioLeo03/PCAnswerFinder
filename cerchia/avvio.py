"""Avvio di Cerchia e Chiedi: icona di notifica e collegamento dei pezzi."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from cerchia import cattura, elementi
from cerchia.schermata import Sessione
from cerchia.tasto_win import TastoWin

TITOLO = "Cerchia e Chiedi"


def _icona() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(217, 119, 87), 8))
    p.drawEllipse(10, 10, 44, 44)
    p.end()
    return QIcon(pix)


class Programma:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.sessione: Sessione | None = None
        self.icona = QSystemTrayIcon(_icona())
        self.icona.setToolTip(f"{TITOLO} — tieni premuto Win")
        self.menu = QMenu()
        esci = QAction("Esci", self.menu)
        esci.triggered.connect(app.quit)
        self.menu.addAction(esci)
        self.icona.setContextMenu(self.menu)
        self.icona.show()
        self.tasto = TastoWin()
        self.tasto.avvia.connect(self.apri)
        self.tasto.attiva()
        app.aboutToQuit.connect(self.tasto.disattiva)

    def avvisa(self, testo: str) -> None:
        self.icona.showMessage(TITOLO, testo)

    def apri(self) -> None:
        if self.sessione is not None:
            return
        try:
            s = Sessione(cattura.fotografa(), elementi.rett_elemento)
        except Exception as e:
            self.avvisa(f"Errore: {e}")
            return
        s.invia.connect(self._invia)
        s.copia.connect(self._copia)
        s.chiusa.connect(self._chiusa)
        self.sessione = s
        s.mostra()

    def _chiusa(self) -> None:
        self.sessione = None

    def _invia(self, png: bytes, messaggio: str) -> None:
        self.sessione.chiudi()
        self.avvisa(f"Da inviare ({len(png)} byte): {messaggio[:80]}")

    def _copia(self, testo: str) -> None:
        self.sessione.chiudi()
        self.avvisa(f"Da copiare: {testo[:80]}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    programma = Programma(app)  # noqa: F841 — tenuto vivo fino all'uscita
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
