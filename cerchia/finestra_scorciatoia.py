"""Finestra per scegliere la scorciatoia che apre PCAnswerFinder."""
from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSlider, QVBoxLayout,
                               QWidget)

from cerchia import scorciatoia
from cerchia.scorciatoia import PREDEFINITA, Scorciatoia

MSG_NON_VALIDA = ("Questa non è una scorciatoia: premi un solo tasto (da tenere premuto) oppure tieni "
                  "premuti Ctrl, Alt, Maiusc o Win e poi un altro tasto.")
IN_ASCOLTO = "Premi la scorciatoia…"

STILE = """
QDialog { background: rgb(32, 33, 36); }
QLabel { color: rgba(255, 255, 255, 200); font-size: 13px; }
QLabel#titolo { color: white; font-size: 18px; font-weight: 600; }
QLabel#avviso { color: rgb(240, 170, 120); }
QPushButton { background: rgba(255, 255, 255, 22); color: white; border: 1px solid rgba(255, 255, 255, 30);
              border-radius: 16px; padding: 7px 16px; font-size: 13px; }
QPushButton:hover { background: rgba(255, 255, 255, 40); }
QPushButton#registra { font-size: 20px; font-weight: 600; padding: 18px; border-radius: 14px;
                       background: rgba(255, 255, 255, 14); border: 2px dashed rgba(255, 255, 255, 60); }
QPushButton#registra[ascolto="true"] { border: 2px solid rgb(217, 119, 87); color: rgb(240, 170, 120); }
QPushButton#salva { background: rgb(217, 119, 87); border: none; }
QPushButton#salva:hover { background: rgb(230, 136, 105); }
QSlider::groove:horizontal { height: 4px; background: rgba(255, 255, 255, 40); border-radius: 2px; }
QSlider::handle:horizontal { width: 16px; margin: -6px 0; border-radius: 8px; background: rgb(217, 119, 87); }
"""


class FinestraScorciatoia(QDialog):
    scelta = Signal(object)  # Scorciatoia salvata

    def __init__(self, tasto, attuale: Scorciatoia, icona: QIcon | None = None) -> None:
        super().__init__(None, Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Scorciatoia di PCAnswerFinder")
        if icona is not None:
            self.setWindowIcon(icona)
        self.setStyleSheet(STILE)
        self.setMinimumWidth(460)
        self._tasto = tasto
        self._scelta = attuale

        colonna = QVBoxLayout(self)
        colonna.setContentsMargins(24, 22, 24, 20)
        colonna.setSpacing(12)
        titolo = QLabel("Scorciatoia per aprire PCAnswerFinder")
        titolo.setObjectName("titolo")
        spiegazione = QLabel("Clicca il riquadro e premi la scorciatoia che vuoi. Un solo tasto si attiva "
                             "tenendolo premuto; con Ctrl, Alt, Maiusc o Win si crea una combinazione.")
        spiegazione.setWordWrap(True)
        self.btn_registra = QPushButton()
        self.btn_registra.setObjectName("registra")
        self.btn_registra.setCursor(Qt.PointingHandCursor)
        self.btn_registra.clicked.connect(self._inizia)

        self._riga_soglia = QWidget()
        riga = QHBoxLayout(self._riga_soglia)
        riga.setContentsMargins(0, 0, 0, 0)
        self.etichetta_soglia = QLabel()
        self.soglia = QSlider(Qt.Horizontal)
        self.soglia.setRange(2, 15)  # decimi di secondo
        self.soglia.valueChanged.connect(self._soglia_cambiata)
        riga.addWidget(self.etichetta_soglia)
        riga.addWidget(self.soglia, 1)

        self.avviso = QLabel()
        self.avviso.setObjectName("avviso")
        self.avviso.setWordWrap(True)

        pulsanti = QHBoxLayout()
        self.btn_predefinita = QPushButton("Ripristina predefinita")
        self.btn_predefinita.clicked.connect(lambda: self._mostra(PREDEFINITA))
        self.btn_annulla = QPushButton("Annulla")
        self.btn_annulla.clicked.connect(self.reject)
        self.btn_salva = QPushButton("Salva")
        self.btn_salva.setObjectName("salva")
        self.btn_salva.clicked.connect(self._salva)
        pulsanti.addWidget(self.btn_predefinita)
        pulsanti.addStretch(1)
        pulsanti.addWidget(self.btn_annulla)
        pulsanti.addWidget(self.btn_salva)

        for w in (titolo, spiegazione, self.btn_registra, self._riga_soglia, self.avviso):
            colonna.addWidget(w)
        colonna.addLayout(pulsanti)
        self._tasto.registrata.connect(self._registrata)
        self._mostra(attuale)

    # ---------- stato mostrato ----------

    def _mostra(self, s: Scorciatoia) -> None:
        self._scelta = s
        self._imposta_ascolto(False)
        self.btn_registra.setText(s.nome())
        self._riga_soglia.setVisible(s.lunga)
        self.soglia.blockSignals(True)
        self.soglia.setValue(round(s.soglia_ms / 100))
        self.soglia.blockSignals(False)
        self._aggiorna_etichetta_soglia()
        testo = s.avviso() or ""
        self.avviso.setText(testo)
        self.avviso.setVisible(bool(testo))

    def _imposta_ascolto(self, attivo: bool) -> None:
        self.btn_registra.setProperty("ascolto", "true" if attivo else "false")
        self.btn_registra.style().unpolish(self.btn_registra)
        self.btn_registra.style().polish(self.btn_registra)
        for b in (self.btn_salva, self.btn_predefinita, self.btn_annulla):
            b.setEnabled(not attivo)

    def _aggiorna_etichetta_soglia(self) -> None:
        secondi = f"{self.soglia.value() / 10:.1f}".replace(".", ",")
        self.etichetta_soglia.setText(f"Tempo da tenere premuto: {secondi} s")

    def _soglia_cambiata(self, valore: int) -> None:
        self._scelta = replace(self._scelta, soglia_ms=valore * 100)
        self._aggiorna_etichetta_soglia()

    # ---------- registrazione ----------

    def _inizia(self) -> None:
        if self._tasto.in_registrazione:
            return
        self.btn_registra.setText(IN_ASCOLTO)
        self.avviso.hide()
        self._imposta_ascolto(True)
        self._tasto.registra()

    def _registrata(self, s) -> None:
        if s is None:
            self._mostra(self._scelta)
            self.avviso.setText(MSG_NON_VALIDA)
            self.avviso.show()
            return
        if s.lunga:
            s = replace(s, soglia_ms=self.soglia.value() * 100)
        self._mostra(s)

    # ---------- chiusura ----------

    def _salva(self) -> None:
        s = self._scelta
        motivo = s.avviso()
        if motivo:
            risposta = QMessageBox.question(self, "Usarla comunque?", f"{motivo}\n\nUsarla comunque?")
            if risposta != QMessageBox.Yes:
                return
        scorciatoia.salva(s)
        self.scelta.emit(s)
        self.accept()

    def done(self, risultato: int) -> None:
        if self._tasto.in_registrazione:
            self._tasto.ferma_registrazione(None)
        try:
            self._tasto.registrata.disconnect(self._registrata)
        except (RuntimeError, TypeError):
            pass
        super().done(risultato)
