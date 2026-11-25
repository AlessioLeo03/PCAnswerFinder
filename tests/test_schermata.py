from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QKeyEvent, QMouseEvent, QPointingDevice
from PySide6.QtWidgets import QApplication

from cerchia.cattura import Foto
from cerchia.gesti import Rett, TipoGesto
from cerchia.destinazione import APERTA, CERCA, NUOVA, Destinazione
from cerchia.schermata import MSG_NESSUN_ELEMENTO, MSG_TITOLO_VUOTO, Schermata


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
    s.invia.connect(lambda png, msg, dest: ricevuti.append((png, msg, dest)))
    _trascina(s, QUADRATO)
    assert s._riquadro is not None
    assert s._tipo is TipoGesto.CERCHIO
    assert not s._barra.isHidden()
    s._campo.setText("Che cos'è?")
    s._invia(False)
    assert len(ricevuti) == 1
    assert len(ricevuti[0][0]) > 0
    assert ricevuti[0][1] == "Che cos'è?"
    assert ricevuti[0][2] == Destinazione(NUOVA, "")
    _chiudi(s)


def _scegli(s, modo):
    s._barra.imposta_modo(modo)


def test_cerca_chat_senza_titolo_non_invia(app):
    s = _crea()
    ricevuti = []
    s.invia.connect(lambda *a: ricevuti.append(a))
    _trascina(s, QUADRATO)
    _scegli(s, CERCA)
    assert s._titolo.isEnabled()
    s._titolo.setText("   ")
    s._invia(False)
    assert ricevuti == []
    assert s._avviso.text() == MSG_TITOLO_VUOTO == "Scrivi il titolo della chat"
    _chiudi(s)


def test_cerca_chat_invia_titolo_e_lo_ricorda(app):
    s = _crea()
    ricevuti = []
    s.invia.connect(lambda *a: ricevuti.append(a))
    _trascina(s, QUADRATO)
    _scegli(s, CERCA)
    s._titolo.setText(" PCAnswerFinder ")
    s._invia(False)
    assert ricevuti[0][2] == Destinazione(CERCA, "PCAnswerFinder")
    _chiudi(s)
    nuova = _crea()
    assert nuova._barra.modo == CERCA
    assert nuova._titolo.text() == "PCAnswerFinder"
    _chiudi(nuova)


def test_chat_aperta_disattiva_titolo(app):
    s = _crea()
    _scegli(s, APERTA)
    assert not s._titolo.isEnabled()
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


def test_suggerimento_dopo_onda_sparisce_al_gesto(app):
    s = _crea()
    s._mostra_suggerimento()
    assert not s._suggerimento.isHidden()
    assert "Cerchia" in s._suggerimento.text()
    _mouse(s, QEvent.MouseButtonPress, 100, 100)
    assert s._suggerimento.isHidden()
    _chiudi(s)


def test_suggerimento_non_compare_con_selezione(app):
    s = _crea()
    _trascina(s, QUADRATO)
    s._mostra_suggerimento()
    assert s._suggerimento.isHidden()
    _chiudi(s)


def test_menu_propone_chat_recenti_attinenti(app):
    from cerchia import destinazione
    for t in ("Spesa", "Progetto PCAnswerFinder", "PC nuovo"):
        destinazione.salva(Destinazione(CERCA, t))
    s = _crea()
    s._barra._aggiorna_suggerimenti("pc")
    assert _voci(s) == ["PC nuovo", "Progetto PCAnswerFinder"]
    assert s._barra.intestazione.text() == "Chat trovate: 2"
    s._barra.lista.itemClicked.emit(s._barra.lista.item(1))
    assert s._barra.destinazione() == Destinazione(CERCA, "Progetto PCAnswerFinder")
    assert s._barra.btn_dove.text().startswith("💬 Progetto PCAnswer")
    _chiudi(s)


def test_menu_propone_anche_le_chat_della_barra_laterale(app, monkeypatch):
    from cerchia import chat_claude
    monkeypatch.setattr(chat_claude, "_titoli", ["Domande Java SE 17", "Gioco di crescita AI in Unity", "3D"])
    s = _crea()
    s._barra._aggiorna_suggerimenti("java")
    assert _voci(s) == ["Domande Java SE 17"]
    s._barra._aggiorna_suggerimenti("cresc")
    assert _voci(s) == ["Gioco di crescita AI in Unity"]
    s._barra._aggiorna_suggerimenti("")
    assert s._barra.intestazione.text() == "Le tue chat: 3"
    assert len(_voci(s)) == 3
    _chiudi(s)


def _voci(s):
    lista = s._barra.lista
    return [lista.item(i).data(Qt.UserRole) for i in range(lista.count())]


def test_elenco_chat_senza_limite_e_con_scorrimento(app, monkeypatch):
    from cerchia import chat_claude
    from cerchia.barra import ALTEZZA_RIGA, RIGHE_VISIBILI
    monkeypatch.setattr(chat_claude, "_titoli", [f"Chat numero {i}" for i in range(30)])
    s = _crea()
    s._barra._aggiorna_suggerimenti("chat")
    assert len(_voci(s)) == 30
    assert s._barra.lista.height() == RIGHE_VISIBILI * ALTEZZA_RIGA + 6
    _chiudi(s)


def test_frecce_e_invio_nel_titolo_scelgono_la_chat(app, monkeypatch):
    from PySide6.QtGui import QKeyEvent
    from cerchia import chat_claude
    monkeypatch.setattr(chat_claude, "_titoli", ["Alfa uno", "Alfa due", "Beta"])
    s = _crea()
    b = s._barra
    b.imposta_modo(CERCA)
    b.titolo.setText("alf")
    b._aggiorna_suggerimenti("alf")
    QApplication.sendEvent(b.titolo, QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier))
    assert b.lista.currentRow() == 1
    b._invio_nel_titolo()
    assert b.destinazione() == Destinazione(CERCA, "Alfa due")
    _chiudi(s)