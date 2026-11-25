"""Avvio di Cerchia e Chiedi: icona di notifica e collegamento dei pezzi."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

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


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icona = QSystemTrayIcon(_icona())
    icona.setToolTip(f"{TITOLO} — tieni premuto Win")
    menu = QMenu()
    esci = QAction("Esci", menu)
    esci.triggered.connect(app.quit)
    menu.addAction(esci)
    icona.setContextMenu(menu)
    icona.show()

    tasto = TastoWin()
    tasto.avvia.connect(lambda: icona.showMessage(TITOLO, "Pressione lunga di Win riconosciuta."))
    tasto.attiva()
    app.aboutToQuit.connect(tasto.disattiva)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
