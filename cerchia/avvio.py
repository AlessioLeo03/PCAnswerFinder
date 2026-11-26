"""Avvio di PCAnswerFinder: icona di notifica e collegamento dei pezzi."""
import logging
import os
import sys
import traceback
import winreg
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from cerchia import appunti, cattura, chat_claude, destinazione, elementi, invio_claude, scorciatoia
from cerchia.finestra_scorciatoia import FinestraScorciatoia
from cerchia.destinazione import Destinazione
from cerchia.schermata import Sessione
from cerchia.tasto_win import TastoWin

TITOLO = "PCAnswerFinder"
CHIAVE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOME_RUN = "PCAnswerFinder"
NOME_RUN_VECCHIO = "CerchiaEChiedi"


def _comando_avvio() -> str:
    if getattr(sys, "frozen", False):  # versione installata con il Setup: un solo .exe
        return f'"{sys.executable}"'
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


def migra_nome_vecchio() -> None:
    """Il programma prima si chiamava "Cerchia e Chiedi": sposta il suo avvio automatico sul nome nuovo."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHIAVE_RUN, 0,
                            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as k:
            winreg.QueryValueEx(k, NOME_RUN_VECCHIO)
            winreg.DeleteValue(k, NOME_RUN_VECCHIO)
            winreg.SetValueEx(k, NOME_RUN, 0, winreg.REG_SZ, _comando_avvio())
    except FileNotFoundError:
        pass
    except OSError:
        logging.exception("migrazione dell'avvio automatico")


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
        migra_nome_vecchio()
        destinazione.migra_vecchie_impostazioni()
        self.icona = QSystemTrayIcon(_icona())
        self.menu = QMenu()
        esci = QAction("Esci", self.menu)
        esci.triggered.connect(app.quit)
        scelta_tasti = QAction("Scorciatoia…", self.menu)
        scelta_tasti.triggered.connect(self.scegli_scorciatoia)
        avvio_win = QAction("Avvia con Windows", self.menu)
        avvio_win.setCheckable(True)
        avvio_win.setChecked(avvio_automatico_attivo())
        avvio_win.toggled.connect(imposta_avvio_automatico)
        self.menu.addAction(scelta_tasti)
        self.menu.addAction(avvio_win)
        self.menu.addSeparator()
        self.menu.addAction(esci)
        self.icona.setContextMenu(self.menu)
        self.icona.show()
        self._finestra_tasti: FinestraScorciatoia | None = None
        self.tasto = TastoWin()
        self.tasto.avvia.connect(self._apri_differito)
        self._usa_scorciatoia(scorciatoia.carica())
        self.tasto.attiva()
        app.aboutToQuit.connect(self.tasto.disattiva)
        chat_claude.aggiorna_in_background()

    def avvisa(self, testo: str) -> None:
        self.icona.showMessage(TITOLO, testo)

    def _usa_scorciatoia(self, s) -> None:
        self.tasto.imposta(s)
        self.icona.setToolTip(f"{TITOLO} — {s.nome()}")

    def scegli_scorciatoia(self) -> None:
        if self._finestra_tasti is not None:
            self._finestra_tasti.raise_()
            self._finestra_tasti.activateWindow()
            return
        f = FinestraScorciatoia(self.tasto, scorciatoia.carica(), _icona())
        f.setAttribute(Qt.WA_DeleteOnClose)
        f.scelta.connect(self._usa_scorciatoia)
        f.scelta.connect(lambda s: self.avvisa(f"Nuova scorciatoia: {s.nome()}"))
        f.finished.connect(lambda _r: setattr(self, "_finestra_tasti", None))
        self._finestra_tasti = f
        f.show()
        f.raise_()
        f.activateWindow()

    def _apri_differito(self) -> None:
        # il lavoro pesante esce dal ciclo del hook di tastiera
        QTimer.singleShot(0, self.apri)

    def apri(self) -> None:
        if self.sessione is not None or self._invio_in_corso:
            return
        chat_claude.aggiorna_in_background()
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

    def _invia(self, png: bytes, messaggio: str, dest: Destinazione) -> None:
        if self._invio_in_corso:
            return
        if self.sessione is not None:
            self.sessione.chiudi()
        self._invio_in_corso = True

        def _esegui() -> None:
            try:
                invio_claude.invia(png, messaggio, self.avvisa, dest)
            finally:
                self._invio_in_corso = False

        QTimer.singleShot(80, _esegui)

    def _copia(self, testo: str) -> None:
        if self.sessione is not None:
            self.sessione.chiudi()
        appunti.metti_testo(testo)
        self.avvisa("Testo copiato.")


def _configura_log() -> None:
    cartella = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "PCAnswerFinder"
    try:
        cartella.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=str(cartella / "errori.log"), level=logging.WARNING, encoding="utf-8",
                            format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    except OSError:
        pass


def _installa_gestore_errori(prendi_programma) -> None:
    def gestore(tipo, valore, tb) -> None:
        try:
            logging.error("Errore non gestito:\n%s", "".join(traceback.format_exception(tipo, valore, tb)))
        except Exception:
            pass
        programma = prendi_programma()
        if programma is None:
            return
        try:
            if programma.sessione is not None:
                programma.sessione.chiudi()
        except Exception:
            logging.exception("errore chiudendo lo strato")
        try:
            programma.avvisa(f"Errore: {valore}")
        except Exception:
            logging.exception("errore nella notifica")

    sys.excepthook = gestore


def main() -> None:
    _configura_log()
    contenitore: list[Programma] = []
    _installa_gestore_errori(lambda: contenitore[0] if contenitore else None)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    programma = Programma(app)
    contenitore.append(programma)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
