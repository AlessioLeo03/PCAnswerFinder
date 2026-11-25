"""Avvio di Cerchia e Chiedi: icona di notifica e collegamento dei pezzi."""
import sys
import winreg
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from cerchia import appunti, cattura, elementi, invio_claude
from cerchia.schermata import Sessione
from cerchia.tasto_win import TastoWin

TITOLO = "Cerchia e Chiedi"
CHIAVE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOME_RUN = "CerchiaEChiedi"


def _comando_avvio() -> str:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    script = Path(__file__).resolve().parent.parent / "avvia.pyw"
    return f'"{pythonw}" "{script}"'


def avvio_automatico_attivo() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHIAVE_RUN) as k:
            winreg.QueryValueEx(k, NOME_RUN)
            return True
    except FileNotFoundError:
        return False


def imposta_avvio_automatico(attivo: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHIAVE_RUN, 0, winreg.KEY_SET_VALUE) as k:
        if attivo:
            winreg.SetValueEx(k, NOME_RUN, 0, winreg.REG_SZ, _comando_avvio())
        else:
            try:
                winreg.DeleteValue(k, NOME_RUN)
            except FileNotFoundError:
                pass


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
        self._invio_in_corso = False
        self.icona = QSystemTrayIcon(_icona())
        self.icona.setToolTip(f"{TITOLO} — tieni premuto Win")
        self.menu = QMenu()
        esci = QAction("Esci", self.menu)
        esci.triggered.connect(app.quit)
        avvio_win = QAction("Avvia con Windows", self.menu)
        avvio_win.setCheckable(True)
        avvio_win.setChecked(avvio_automatico_attivo())
        avvio_win.toggled.connect(imposta_avvio_automatico)
        self.menu.addAction(avvio_win)
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
        if self.sessione is not None or self._invio_in_corso:
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
        if self._invio_in_corso:
            return
        if self.sessione is not None:
            self.sessione.chiudi()
        self._invio_in_corso = True

        def _esegui() -> None:
            try:
                invio_claude.invia(png, messaggio, self.avvisa)
            finally:
                self._invio_in_corso = False

        QTimer.singleShot(80, _esegui)

    def _copia(self, testo: str) -> None:
        if self.sessione is not None:
            self.sessione.chiudi()
        appunti.metti_testo(testo)
        self.avvisa("Testo copiato.")


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    programma = Programma(app)  # noqa: F841 — tenuto vivo fino all'uscita
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
