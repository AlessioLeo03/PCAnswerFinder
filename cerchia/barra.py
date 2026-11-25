"""Barra in basso dello strato, in stile Android: chip sopra, pillola con domanda, scelta della chat e invio."""
from PySide6.QtCore import QEvent, QPoint, QPointF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QActionGroup, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu,
                               QPushButton, QToolButton, QVBoxLayout, QWidget, QWidgetAction)

from cerchia import chat_claude, destinazione

ARANCIO = QColor(217, 119, 87)
RIGHE_VISIBILI = 7   # chat visibili nell'elenco prima di dover scorrere
ALTEZZA_RIGA = 34

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
QWidget#pannello { background: transparent; }
QLabel#intestazione { color: rgba(255, 255, 255, 120); font-size: 12px; padding: 6px 12px 2px 12px; }
QListWidget#listaChat { background: transparent; border: none; color: white; font-size: 14px; outline: none;
                        margin: 0 4px 2px 4px; }
QListWidget#listaChat::item { height: 34px; padding: 0 10px; border-radius: 8px; }
QListWidget#listaChat::item:hover { background: rgba(255, 255, 255, 18); }
QListWidget#listaChat::item:selected { background: rgba(255, 255, 255, 34); color: white; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(255, 255, 255, 70); border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
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
        self.titolo.returnPressed.connect(self._invio_nel_titolo)
        self.titolo.textEdited.connect(self._aggiorna_suggerimenti)
        self.titolo.textChanged.connect(lambda _t: self.imposta_modo(self.modo))
        self.titolo.installEventFilter(self)
        # pannello di altezza fissa: casella + intestazione + elenco che scorre
        pannello = QWidget()
        pannello.setObjectName("pannello")
        colonna = QVBoxLayout(pannello)
        colonna.setContentsMargins(0, 0, 0, 0)
        colonna.setSpacing(2)
        self.intestazione = QLabel()
        self.intestazione.setObjectName("intestazione")
        self.lista = QListWidget()
        self.lista.setObjectName("listaChat")
        self.lista.setFixedHeight(RIGHE_VISIBILI * ALTEZZA_RIGA + 6)
        self.lista.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lista.setTextElideMode(Qt.ElideRight)
        self.lista.itemClicked.connect(lambda voce: self.scegli_chat(voce.data(Qt.UserRole)))
        self.lista.itemActivated.connect(lambda voce: self.scegli_chat(voce.data(Qt.UserRole)))
        colonna.addWidget(self.titolo)
        colonna.addWidget(self.intestazione)
        colonna.addWidget(self.lista)
        contenitore = QWidgetAction(self.menu)
        contenitore.setDefaultWidget(pannello)
        self.menu.addAction(contenitore)
        self.menu.aboutToShow.connect(lambda: self._aggiorna_suggerimenti(self.titolo.text()))
        self.btn_dove.setMenu(self.menu)

    def _aggiorna_suggerimenti(self, testo: str) -> None:
        """Tutte le chat attinenti a quanto scritto (cercate in passato + barra laterale), in un elenco che scorre."""
        elenco = destinazione.unisci(destinazione.recenti(), chat_claude.titoli())
        titoli = destinazione.suggerimenti(elenco, testo, quanti=None)
        self.lista.clear()
        for t in titoli:
            voce = QListWidgetItem(f"💬  {t}")
            voce.setData(Qt.UserRole, t)
            voce.setToolTip(t)
            self.lista.addItem(voce)
        if titoli:
            self.lista.setCurrentRow(0)
        if not elenco:
            self.intestazione.setText("Nessuna chat letta da Claude: scrivi il titolo")
        elif not titoli:
            self.intestazione.setText("Nessuna chat trovata")
        elif testo.strip():
            self.intestazione.setText(f"Chat trovate: {len(titoli)}")
        else:
            self.intestazione.setText(f"Le tue chat: {len(titoli)}")

    def _invio_nel_titolo(self) -> None:
        """Invio nella casella: se il testo non è già un titolo esatto, sceglie la prima chat trovata."""
        voce = self.lista.currentItem()
        esatto = any(self.lista.item(i).data(Qt.UserRole) == self.titolo.text().strip()
                     for i in range(self.lista.count()))
        if voce is not None and not esatto:
            self.scegli_chat(voce.data(Qt.UserRole))
        else:
            self.menu.close()

    def eventFilter(self, oggetto, evento) -> bool:
        # frecce su/giù nella casella del titolo: si muove nell'elenco
        if oggetto is self.titolo and evento.type() == QEvent.KeyPress and self.lista.count():
            passo = {Qt.Key_Down: 1, Qt.Key_Up: -1}.get(evento.key())
            if passo:
                riga = max(0, min(self.lista.count() - 1, self.lista.currentRow() + passo))
                self.lista.setCurrentRow(riga)
                return True
        return super().eventFilter(oggetto, evento)

    def scegli_chat(self, titolo: str) -> None:
        self.titolo.setText(titolo)
        self.imposta_modo(destinazione.CERCA)
        self.menu.close()

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
