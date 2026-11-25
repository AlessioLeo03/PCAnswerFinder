"""Barra in basso dello strato, in stile Android: chip sopra, pillola con domanda, scelta della chat e invio."""
from PySide6.QtCore import QPoint, QPointF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QActionGroup, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QToolButton,
                               QVBoxLayout, QWidgetAction)

from cerchia import destinazione

ARANCIO = QColor(217, 119, 87)

STILE = """
QFrame#pillola { background: rgba(32, 33, 36, 240); border: 1px solid rgba(255, 255, 255, 28);
                 border-radius: 30px; }
QLineEdit#campo { background: transparent; border: none; color: white; font-size: 16px; padding: 0 6px;
                  selection-background-color: rgba(217, 119, 87, 160); }
QPushButton#chip { background: rgba(32, 33, 36, 240); color: white; border: 1px solid rgba(255, 255, 255, 40);
                   border-radius: 17px; padding: 7px 16px; font-size: 13px; }
QPushButton#chip:hover { background: rgba(60, 62, 67, 245); }
QPushButton#chip:disabled { color: rgba(255, 255, 255, 80); border-color: rgba(255, 255, 255, 18); }
QToolButton#dove { background: rgba(255, 255, 255, 18); color: rgba(255, 255, 255, 210); border: none;
                   border-radius: 16px; padding: 6px 12px; font-size: 13px; }
QToolButton#dove:hover { background: rgba(255, 255, 255, 40); }
QToolButton#dove::menu-indicator { image: none; width: 0; }
QToolButton#invia { background: rgb(217, 119, 87); border: none; border-radius: 22px; }
QToolButton#invia:hover { background: rgb(230, 136, 105); }
QMenu#menuDove { background: rgb(40, 41, 45); color: white; border: 1px solid rgba(255, 255, 255, 30);
                 border-radius: 14px; padding: 6px; font-size: 14px; }
QMenu#menuDove::item { padding: 8px 18px 8px 30px; border-radius: 8px; }
QMenu#menuDove::item:selected { background: rgba(255, 255, 255, 30); }
QMenu#menuDove::item:disabled { color: rgba(255, 255, 255, 110); font-size: 12px; padding: 6px 18px 2px 30px; }
QMenu#menuDove::indicator { left: 10px; width: 12px; height: 12px; }
QMenu#menuDove::separator { height: 1px; background: rgba(255, 255, 255, 30); margin: 6px 8px; }
QLineEdit#titolo { background: rgba(255, 255, 255, 22); border: 1px solid rgba(255, 255, 255, 40);
                   border-radius: 10px; color: white; font-size: 14px; padding: 6px 10px; margin: 2px 6px 4px 6px; }
QLineEdit#titolo:disabled { color: rgba(255, 255, 255, 80); border-color: rgba(255, 255, 255, 15); }
"""


def icona_claude(lato: int = 22) -> QPixmap:
    """Piccola stella a raggi nel colore di Claude."""
    pix = QPixmap(lato * 2, lato * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(ARANCIO, lato * 0.13, Qt.SolidLine, Qt.RoundCap))
    c = lato / 2
    for i in range(12):
        lungo = 0.46 if i % 2 == 0 else 0.34
        p.save()
        p.translate(c, c)
        p.rotate(i * 30)
        p.drawLine(QPointF(0, lato * 0.10), QPointF(0, lato * lungo))
        p.restore()
    p.end()
    return pix


def _icona_freccia(lato: int = 20) -> QIcon:
    pix = QPixmap(lato * 2, lato * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("white"), lato * 0.13, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    percorso = QPainterPath(QPointF(lato * 0.5, lato * 0.82))
    percorso.lineTo(lato * 0.5, lato * 0.2)
    percorso.moveTo(lato * 0.24, lato * 0.44)
    percorso.lineTo(lato * 0.5, lato * 0.18)
    percorso.lineTo(lato * 0.76, lato * 0.44)
    p.drawPath(percorso)
    p.end()
    return QIcon(pix)


class Barra(QFrame):
    """Contenitore trasparente: riga di chip (Traduci, Copia testo) e pillola della domanda."""

    invia_richiesto = Signal(bool)  # True = Traduci
    copia_richiesta = Signal()

    ALTEZZA = 60 + 10 + 34

    def __init__(self, genitore) -> None:
        super().__init__(genitore)
        self.setObjectName("barra")
        self.setStyleSheet(STILE)
        colonna = QVBoxLayout(self)
        colonna.setContentsMargins(0, 0, 0, 0)
        colonna.setSpacing(10)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.btn_traduci = QPushButton("文A   Traduci")
        self.btn_copia = QPushButton("⧉   Copia testo")
        for b in (self.btn_traduci, self.btn_copia):
            b.setObjectName("chip")
            b.setCursor(Qt.PointingHandCursor)
            chips.addWidget(b)
        chips.addStretch(1)
        self.btn_traduci.clicked.connect(lambda: self.invia_richiesto.emit(True))
        self.btn_copia.clicked.connect(self.copia_richiesta)
        colonna.addLayout(chips)

        pillola = QFrame()
        pillola.setObjectName("pillola")
        pillola.setFixedHeight(60)
        riga = QHBoxLayout(pillola)
        riga.setContentsMargins(18, 8, 8, 8)
        riga.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(icona_claude())
        logo.setStyleSheet("background: transparent;")
        self.campo = QLineEdit()
        self.campo.setObjectName("campo")
        self.campo.setPlaceholderText("Chiedi a Claude su questa selezione…")
        self.campo.returnPressed.connect(lambda: self.invia_richiesto.emit(False))
        self._crea_menu()
        self.btn_invia = QToolButton()
        self.btn_invia.setObjectName("invia")
        self.btn_invia.setFixedSize(44, 44)
        self.btn_invia.setIcon(_icona_freccia())
        self.btn_invia.setIconSize(QSize(20, 20))
        self.btn_invia.setCursor(Qt.PointingHandCursor)
        self.btn_invia.setToolTip("Invia a Claude")
        self.btn_invia.clicked.connect(lambda: self.invia_richiesto.emit(False))
        riga.addWidget(logo)
        riga.addWidget(self.campo, 1)
        riga.addWidget(self.btn_dove)
        riga.addWidget(self.btn_invia)
        colonna.addWidget(pillola)

        scelta = destinazione.carica()
        self.titolo.setText(scelta.titolo)
        self.imposta_modo(scelta.modo)

    def _crea_menu(self) -> None:
        self.btn_dove = QToolButton()
        self.btn_dove.setObjectName("dove")
        self.btn_dove.setCursor(Qt.PointingHandCursor)
        self.btn_dove.setPopupMode(QToolButton.InstantPopup)
        self.menu = QMenu(self.btn_dove)
        self.menu.setObjectName("menuDove")
        self.menu.setWindowFlags(self.menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.menu.setAttribute(Qt.WA_TranslucentBackground)
        self.menu.setStyleSheet(STILE)
        gruppo = QActionGroup(self.menu)
        self._azioni = {}
        for valore, etichetta in destinazione.VOCI:
            azione = self.menu.addAction(etichetta)
            azione.setCheckable(True)
            azione.setData(valore)
            gruppo.addAction(azione)
            azione.triggered.connect(lambda _c=False, v=valore: self._scelta_dal_menu(v))
            self._azioni[valore] = azione
        self.menu.addSeparator()
        self.titolo = QLineEdit()
        self.titolo.setObjectName("titolo")
        self.titolo.setPlaceholderText("Titolo della chat da cercare")
        self.titolo.setMinimumWidth(240)
        self.titolo.returnPressed.connect(self.menu.close)
        self.titolo.textEdited.connect(self._aggiorna_suggerimenti)
        self.titolo.textChanged.connect(lambda _t: self.imposta_modo(self.modo))
        contenitore = QWidgetAction(self.menu)
        contenitore.setDefaultWidget(self.titolo)
        self.menu.addAction(contenitore)
        self._suggeriti: list = []
        self.menu.aboutToShow.connect(lambda: self._aggiorna_suggerimenti(self.titolo.text()))
        self.btn_dove.setMenu(self.menu)

    def _aggiorna_suggerimenti(self, testo: str) -> None:
        """Sotto la casella del titolo: le chat cercate in passato più attinenti a quanto scritto."""
        for azione in self._suggeriti:
            self.menu.removeAction(azione)
            azione.deleteLater()
        self._suggeriti = []
        titoli = destinazione.suggerimenti(destinazione.recenti(), testo)
        if not titoli:
            return
        intestazione = self.menu.addAction("Recenti" if not testo.strip() else "Chat trovate")
        intestazione.setEnabled(False)
        self._suggeriti.append(intestazione)
        for t in titoli:
            azione = self.menu.addAction(f"💬  {t}")
            azione.triggered.connect(lambda _c=False, t=t: self.scegli_chat(t))
            self._suggeriti.append(azione)
        self.menu.adjustSize()

    def scegli_chat(self, titolo: str) -> None:
        self.titolo.setText(titolo)
        self.imposta_modo(destinazione.CERCA)

    # ---------- scelta della chat ----------

    @property
    def modo(self) -> str:
        for valore, azione in self._azioni.items():
            if azione.isChecked():
                return valore
        return destinazione.NUOVA

    def imposta_modo(self, modo: str) -> None:
        azione = self._azioni.get(modo, self._azioni[destinazione.NUOVA])
        azione.setChecked(True)
        cerca = azione.data() == destinazione.CERCA
        self.titolo.setEnabled(cerca)
        if cerca and self.titolo.text().strip():
            etichetta = self.titolo.text().strip()
            if len(etichetta) > 22:
                etichetta = etichetta[:21] + "…"
            etichetta = f"💬 {etichetta}"
        else:
            etichetta = dict(destinazione.VOCI)[azione.data()].rstrip("…")
        self.btn_dove.setText(f"{etichetta}  ▾")

    def _scelta_dal_menu(self, modo: str) -> None:
        self.imposta_modo(modo)
        if modo == destinazione.CERCA:
            QTimer.singleShot(0, self.chiedi_titolo)  # dopo la chiusura del menu

    def chiedi_titolo(self) -> None:
        """Riapre il menu con la casella del titolo pronta per scrivere."""
        sopra = QPoint(0, self.menu.sizeHint().height() + 6)
        self.menu.popup(self.btn_dove.mapToGlobal(QPoint(0, 0)) - sopra)
        self.titolo.setFocus()
        self.titolo.selectAll()

    def destinazione(self) -> destinazione.Destinazione:
        return destinazione.Destinazione(self.modo, self.titolo.text().strip())
