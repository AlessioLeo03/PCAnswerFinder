"""Strato a tutto schermo: foto congelata, luccichio, gesti e barra della domanda."""
from collections.abc import Callable
from math import hypot

from PySide6.QtCore import QEasingCurve, QObject, QPointF, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from cerchia import gesti
from cerchia.cattura import Foto, ritaglio_png
from cerchia.gesti import Parola, Rett, TipoGesto
from cerchia.messaggio import componi
from cerchia.ocr import LettoreOcr

TrovaElemento = Callable[[int, int], Rett | None]

AZZURRO = QColor(80, 150, 255, 110)
BUIO_MAX = 110     # oscuramento senza selezione (0-255)
BUIO_FUORI = 160   # oscuramento fuori dal riquadro selezionato
RAGGIO_MANIGLIA = 24
MSG_OCR_ASSENTE = "Testo non disponibile: in Windows manca la lingua per il riconoscimento del testo."
MSG_NESSUN_ELEMENTO = "Nessun elemento qui, prova a cerchiare."

STILE = """
QFrame#barra { background: rgba(32, 33, 36, 235); border-radius: 28px; }
QLineEdit { background: transparent; border: none; color: white; font-size: 16px; padding: 0 12px; }
QPushButton { background: rgba(255, 255, 255, 30); color: white; border: none; border-radius: 18px;
              padding: 8px 14px; font-size: 14px; }
QPushButton:hover { background: rgba(255, 255, 255, 55); }
QPushButton:disabled { color: rgba(255, 255, 255, 90); }
QLabel#avviso { background: rgba(32, 33, 36, 235); color: white; border-radius: 14px;
                padding: 8px 14px; font-size: 14px; }
"""


def _qrect(r: Rett) -> QRectF:
    return QRectF(r.x, r.y, r.w, r.h)


class Schermata(QWidget):
    gesto_iniziato = Signal()
    invia = Signal(bytes, str)
    copia = Signal(str)
    esci = Signal()

    def __init__(self, foto: Foto, trova_elemento: TrovaElemento) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(foto.schermo.geometry())
        self._foto = foto
        self._trova_elemento = trova_elemento
        self._dpr = foto.dpr
        self._limite = Rett(0, 0, foto.immagine.width(), foto.immagine.height())
        self._parole: list[Parola] = []
        self._ocr = "in_corso"  # "in_corso" | "ok" | "assente"
        self._punti: list[tuple[float, float]] = []
        self._tipo: TipoGesto | None = None
        self._riquadro: Rett | None = None
        self._sel: list[Parola] = []
        self._maniglia: int | None = None
        self._buio = 0.0
        self._luce = -1.0
        self._crea_barra()
        self._crea_animazioni()
        self._lettore = LettoreOcr(self)
        self._lettore.pronto.connect(self._ocr_pronto)
        self._lettore.avvia(foto.immagine)

    # ---------- costruzione ----------

    def _crea_barra(self) -> None:
        self.setStyleSheet(STILE)
        self._barra = QFrame(self)
        self._barra.setObjectName("barra")
        riga = QHBoxLayout(self._barra)
        riga.setContentsMargins(16, 8, 8, 8)
        riga.setSpacing(8)
        self._campo = QLineEdit()
        self._campo.setPlaceholderText("Chiedi a Claude su questa selezione…")
        self._campo.returnPressed.connect(lambda: self._invia(False))
        self._btn_traduci = QPushButton("Traduci")
        self._btn_traduci.clicked.connect(lambda: self._invia(True))
        self._btn_copia = QPushButton("Copia testo")
        self._btn_copia.clicked.connect(self._copia)
        self._btn_invia = QPushButton("Invia")
        self._btn_invia.clicked.connect(lambda: self._invia(False))
        for w in (self._campo, self._btn_traduci, self._btn_copia, self._btn_invia):
            riga.addWidget(w)
        riga.setStretch(0, 1)
        self._barra.hide()
        self._avviso = QLabel(self)
        self._avviso.setObjectName("avviso")
        self._avviso.hide()

    def _crea_animazioni(self) -> None:
        self._anim_buio = QVariantAnimation(self)
        self._anim_buio.setStartValue(0.0)
        self._anim_buio.setEndValue(1.0)
        self._anim_buio.setDuration(200)
        self._anim_buio.valueChanged.connect(self._imposta_buio)
        self._anim_luce = QVariantAnimation(self)
        self._anim_luce.setStartValue(-0.3)
        self._anim_luce.setEndValue(1.3)
        self._anim_luce.setDuration(900)
        self._anim_luce.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim_luce.valueChanged.connect(self._imposta_luce)
        self._anim_luce.finished.connect(lambda: self._imposta_luce(-1.0))

    def _imposta_buio(self, v: float) -> None:
        self._buio = v
        self.update()

    def _imposta_luce(self, v: float) -> None:
        self._luce = v
        self.update()

    # ---------- interfaccia pubblica ----------

    def mostra(self, attiva: bool) -> None:
        self.show()
        self.raise_()
        if attiva:
            self.activateWindow()
        self._anim_buio.start()
        self._anim_luce.start()

    def azzera(self) -> None:
        self._punti = []
        self._tipo = None
        self._riquadro = None
        self._sel = []
        self._maniglia = None
        self._barra.hide()
        self._avviso.hide()
        self.update()

    # ---------- mouse e tastiera ----------

    def _px(self, ev) -> tuple[float, float]:
        p = ev.position()
        return (p.x() * self._dpr, p.y() * self._dpr)

    def _maniglia_vicina(self, p: tuple[float, float]) -> int | None:
        r = self._riquadro
        angoli = [(r.x, r.y), (r.destra, r.y), (r.x, r.basso), (r.destra, r.basso)]
        for i, a in enumerate(angoli):
            if hypot(p[0] - a[0], p[1] - a[1]) <= RAGGIO_MANIGLIA * self._dpr:
                return i
        return None

    def mousePressEvent(self, ev) -> None:
        if ev.button() != Qt.LeftButton:
            return
        p = self._px(ev)
        self._avviso.hide()
        if self._riquadro is not None:
            self._maniglia = self._maniglia_vicina(p)
            if self._maniglia is not None:
                return
        self.gesto_iniziato.emit()
        self.azzera()
        self._punti = [p]
        self.update()

    def mouseMoveEvent(self, ev) -> None:
        p = self._px(ev)
        if self._maniglia is not None:
            self._riquadro = gesti.sposta_angolo(self._riquadro, self._maniglia, p, self._limite)
        elif self._punti:
            self._punti.append(p)
        self.update()

    def mouseReleaseEvent(self, ev) -> None:
        if ev.button() != Qt.LeftButton:
            return
        if self._maniglia is not None:
            self._maniglia = None
            self._tipo = TipoGesto.CERCHIO
            self._aggiorna_sel()
            self._mostra_barra()
            return
        if not self._punti:
            return
        punti, self._punti = self._punti, []
        tipo = gesti.classifica(punti, self._parole)
        if tipo is TipoGesto.CLIC:
            r = self._elemento(punti[0])
            if r is None:
                self._mostra_avviso(MSG_NESSUN_ELEMENTO)
                self.update()
                return
            self._riquadro = r
        elif tipo is TipoGesto.TESTO:
            i0 = gesti.indice_parola(punti[0], self._parole)
            i1 = gesti.indice_parola_vicina(punti[-1], self._parole)
            self._sel = gesti.parole_tra(self._parole, i0, i1)
            self._riquadro = gesti.riquadro_parole(self._sel, self._limite)
        else:
            self._riquadro = gesti.riquadro_da_tratto(punti, self._limite)
        self._tipo = tipo
        if tipo is not TipoGesto.TESTO:
            self._aggiorna_sel()
        self._mostra_barra()

    def keyPressEvent(self, ev) -> None:
        if ev.key() == Qt.Key_Escape:
            self.esci.emit()
        else:
            super().keyPressEvent(ev)

    # ---------- selezione ----------

    def _elemento(self, p: tuple[float, float]) -> Rett | None:
        ox, oy = self._foto.origine
        r = self._trova_elemento(int(ox + p[0]), int(oy + p[1]))
        if r is None:
            return None
        locale = Rett(r.x - ox, r.y - oy, r.w, r.h).dentro(self._limite)
        area = locale.w * locale.h
        if area <= 0 or area > 0.9 * self._limite.w * self._limite.h:
            return None
        return locale

    def _aggiorna_sel(self) -> None:
        if self._riquadro is not None:
            self._sel = gesti.parole_dentro(self._parole, self._riquadro)
        self._aggiorna_pulsanti()

    def _ocr_pronto(self, parole: list[Parola] | None) -> None:
        if parole is None:
            self._ocr = "assente"
            self._parole = []
            if self._barra.isVisible():
                self._mostra_avviso(MSG_OCR_ASSENTE)
        else:
            self._ocr = "ok"
            self._parole = parole
            if self._riquadro is not None and self._tipo is not TipoGesto.TESTO:
                self._aggiorna_sel()
        self._aggiorna_pulsanti()

    def _aggiorna_pulsanti(self) -> None:
        self._btn_traduci.setEnabled(self._ocr != "assente")
        self._btn_copia.setEnabled(bool(self._sel))

    # ---------- barra e avvisi ----------

    def _mostra_barra(self) -> None:
        larghezza = min(720, self.width() - 32)
        altezza = 56
        self._barra.setGeometry((self.width() - larghezza) // 2, self.height() - altezza - 40, larghezza, altezza)
        self._aggiorna_pulsanti()
        self._barra.show()
        self._barra.raise_()
        if self._ocr == "assente":
            self._mostra_avviso(MSG_OCR_ASSENTE)
        self.activateWindow()
        self._campo.setFocus()
        self.update()

    def _mostra_avviso(self, testo: str) -> None:
        self._avviso.setText(testo)
        self._avviso.adjustSize()
        base = self._barra.y() if self._barra.isVisible() else self.height() - 40
        self._avviso.move((self.width() - self._avviso.width()) // 2, base - self._avviso.height() - 12)
        self._avviso.show()
        self._avviso.raise_()

    def _invia(self, traduci: bool) -> None:
        if self._riquadro is None:
            return
        testo = gesti.testo_di(self._sel)
        messaggio = componi(self._campo.text(), testo, traduci)
        png = ritaglio_png(self._foto.immagine, self._riquadro)
        if not png:
            return
        self.invia.emit(png, messaggio)

    def _copia(self) -> None:
        testo = gesti.testo_di(self._sel)
        if testo:
            self.copia.emit(testo)

    # ---------- disegno ----------

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(1 / self._dpr, 1 / self._dpr)  # da qui in poi: pixel fisici
        p.drawImage(0, 0, self._foto.immagine)
        w, h = self._limite.w, self._limite.h
        tutto = QPainterPath()
        tutto.addRect(0, 0, w, h)
        if self._riquadro is not None:
            raggio = 16 * self._dpr
            buco = QPainterPath()
            buco.addRoundedRect(_qrect(self._riquadro), raggio, raggio)
            p.fillPath(tutto.subtracted(buco), QColor(0, 0, 0, int(BUIO_FUORI * self._buio)))
        else:
            p.fillPath(tutto, QColor(0, 0, 0, int(BUIO_MAX * self._buio)))
        if self._luce > -0.5:
            self._disegna_luce(p, w, h)
        if self._tipo is TipoGesto.TESTO:
            for parola in self._sel:
                p.fillRect(_qrect(parola.rett), AZZURRO)
        if len(self._punti) > 1:
            self._disegna_tratto(p)
        if self._riquadro is not None:
            self._disegna_riquadro(p)
        p.end()

    def _disegna_luce(self, p: QPainter, w: float, h: float) -> None:
        centro = self._luce * (w + h)
        banda = 300 * self._dpr
        g = QLinearGradient(centro - banda, 0, centro, h)
        g.setColorAt(0.0, QColor(255, 255, 255, 0))
        g.setColorAt(0.5, QColor(255, 255, 255, 70))
        g.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(QRectF(0, 0, w, h), g)

    def _disegna_tratto(self, p: QPainter) -> None:
        percorso = QPainterPath(QPointF(*self._punti[0]))
        for q in self._punti[1:]:
            percorso.lineTo(QPointF(*q))
        for larghezza, alfa in ((22, 50), (12, 110), (5, 255)):
            penna = QPen(QColor(255, 255, 255, alfa), larghezza * self._dpr, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.strokePath(percorso, penna)

    def _disegna_riquadro(self, p: QPainter) -> None:
        raggio = 16 * self._dpr
        p.setPen(QPen(QColor(255, 255, 255), 3 * self._dpr))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(_qrect(self._riquadro), raggio, raggio)
        p.setBrush(QColor(255, 255, 255))
        r = self._riquadro
        for x, y in ((r.x, r.y), (r.destra, r.y), (r.x, r.basso), (r.destra, r.basso)):
            p.drawEllipse(QPointF(x, y), 7 * self._dpr, 7 * self._dpr)


class Sessione(QObject):
    """Uno strato per ogni schermo; una sola selezione alla volta."""

    invia = Signal(bytes, str)
    copia = Signal(str)
    chiusa = Signal()

    def __init__(self, foto: list[Foto], rett_elemento: Callable[[int, int, list[int]], Rett | None]) -> None:
        super().__init__()
        self._schermate: list[Schermata] = []
        self._chiusa = False

        def trova(x: int, y: int) -> Rett | None:
            return rett_elemento(x, y, [int(s.winId()) for s in self._schermate])

        for f in foto:
            s = Schermata(f, trova)
            s.gesto_iniziato.connect(lambda s=s: self._azzera_altre(s))
            s.invia.connect(self.invia)
            s.copia.connect(self.copia)
            s.esci.connect(self.chiudi)
            self._schermate.append(s)

    def mostra(self) -> None:
        schermo_mouse = QCursor.pos()
        for s in self._schermate:
            s.mostra(attiva=s.geometry().contains(schermo_mouse))

    def _azzera_altre(self, attiva: Schermata) -> None:
        for s in self._schermate:
            if s is not attiva:
                s.azzera()

    def chiudi(self) -> None:
        if self._chiusa:
            return
        self._chiusa = True
        for s in self._schermate:
            s.close()
            s.deleteLater()
        self._schermate.clear()
        self.chiusa.emit()
