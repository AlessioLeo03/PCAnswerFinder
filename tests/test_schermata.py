from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QKeyEvent, QMouseEvent, QPointingDevice
from PySide6.QtWidgets import QApplication

from cerchia.cattura import Foto
from cerchia.gesti import Rett, TipoGesto
from cerchia.schermata import MSG_NESSUN_ELEMENTO, Schermata


def _crea(trova=lambda x, y: None):
    img = QImage(800, 600, QImage.Format_RGB32)
    img.fill(QColor("white"))
    foto = Foto(QGuiApplication.primaryScreen(), img, (0, 0), 1.0)
    s = Schermata(foto, trova)
    s.resize(800, 600)
    s._parole = []
    s._ocr = "ok"
    return s


def _mouse(s, tipo, x, y):
    pt = QPointF(x, y)
    bottone = Qt.LeftButton
    stato = Qt.LeftButton if tipo != QEvent.MouseButtonRelease else Qt.NoButton
    ev = QMouseEvent(tipo, pt, s.mapToGlobal(pt), bottone, stato, Qt.NoModifier, QPointingDevice.primaryPointingDevice())
    QApplication.sendEvent(s, ev)


def _trascina(s, percorso):
    _mouse(s, QEvent.MouseButtonPress, *percorso[0])
    for p in percorso[1:]:
        _mouse(s, QEvent.MouseMove, *p)
    _mouse(s, QEvent.MouseButtonRelease, *percorso[-1])


def _chiudi(s):
    s.close()
    s.deleteLater()


QUADRATO = [(100, 100), (200, 100), (300, 100), (300, 200), (300, 300), (200, 300), (100, 300), (100, 200), (100, 100)]


def test_cerchio_mostra_barra_e_invia(app):
    s = _crea()
    ricevuti = []
    s.invia.connect(lambda png, msg: ricevuti.append((png, msg)))
    _trascina(s, QUADRATO)
    assert s._riquadro is not None
    assert s._tipo is TipoGesto.CERCHIO
    assert not s._barra.isHidden()
    s._campo.setText("Che cos'è?")
    s._invia(False)
    assert len(ricevuti) == 1
    assert len(ricevuti[0][0]) > 0
    assert ricevuti[0][1] == "Che cos'è?"
    _chiudi(s)


def test_clic_su_elemento(app):
    s = _crea(lambda x, y: Rett(50, 60, 200, 100))
    _trascina(s, [(150, 100)])
    assert s._riquadro == Rett(50, 60, 200, 100)
    assert s._tipo is TipoGesto.CLIC
    _chiudi(s)


def test_clic_senza_elemento(app):
    s = _crea(lambda x, y: None)
    _trascina(s, [(150, 100)])
    assert s._riquadro is None
    assert not s._avviso.isHidden()
    assert s._avviso.text() == MSG_NESSUN_ELEMENTO == "Nessun elemento qui, prova a cerchiare."
    _chiudi(s)


def test_esc_emette_esci(app):
    s = _crea()
    visti = []
    s.esci.connect(lambda: visti.append(1))
    QApplication.sendEvent(s, QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
    assert visti == [1]
    _chiudi(s)


def test_clic_sulla_barra_non_cancella_la_selezione(app):
    s = _crea()
    _trascina(s, QUADRATO)
    prima = s._riquadro
    assert prima is not None
    for x in (2, s._barra.width() // 2):
        pt = QPointF(x, 2)
        for tipo, stato in ((QEvent.MouseButtonPress, Qt.LeftButton), (QEvent.MouseButtonRelease, Qt.NoButton)):
            ev = QMouseEvent(tipo, pt, s._barra.mapToGlobal(pt), Qt.LeftButton, stato, Qt.NoModifier,
                             QPointingDevice.primaryPointingDevice())
            QApplication.sendEvent(s._barra, ev)
    assert s._riquadro == prima
    _chiudi(s)
