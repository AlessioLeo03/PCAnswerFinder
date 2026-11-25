r"""Video di anteprima (MP4, 1280x720, 30 fps) per presentare PCAnswerFinder.

Usa lo strato vero del programma (Schermata e Barra) sopra un desktop di esempio disegnato qui:
niente registrazione dello schermo, niente dati personali. Codifica con QtMultimedia (FFmpeg di Qt).

Uso:  .\.venv\Scripts\python pacchetto\video_anteprima.py [--scena grafico|codice] [--uscita file.mp4]
           [--campioni cartella] [--passo 30]
"""
import math
import sys
import tempfile
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from PySide6.QtCore import QEvent, QPointF, QRectF, QSettings, Qt, QUrl  # noqa: E402
from PySide6.QtGui import (QColor, QFont, QGuiApplication, QImage, QLinearGradient, QMouseEvent,  # noqa: E402
                           QPainter, QPainterPath, QPen, QPointingDevice, QPolygonF, QRadialGradient)
from PySide6.QtMultimedia import (QMediaCaptureSession, QMediaFormat, QMediaRecorder, QVideoFrame,  # noqa: E402
                                  QVideoFrameFormat, QVideoFrameInput)
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv)

from cerchia import chat_claude, destinazione  # noqa: E402

# impostazioni pulite: il video non deve mostrare titoli di chat dell'utente
_ini = str(Path(tempfile.mkdtemp()) / "video.ini")
destinazione._impostazioni = lambda: QSettings(_ini, QSettings.IniFormat)
chat_claude._titoli = []

from cerchia.barra import icona_claude  # noqa: E402
from cerchia.cattura import Foto  # noqa: E402
from cerchia.schermata import Schermata  # noqa: E402

L, A, FPS = 1280, 720, 30


def _opzione(nome: str, predefinito: str | None = None) -> str | None:
    if nome in sys.argv[1:-1]:
        return sys.argv[sys.argv.index(nome) + 1]
    return predefinito


SCENA = _opzione("--scena", "grafico")
# cartella dove salvare un fotogramma ogni PASSO, per controllare il video senza aprirlo
CAMPIONI = Path(_opzione("--campioni")) if _opzione("--campioni") else None
PASSO = int(_opzione("--passo", "30"))
ARANCIO = QColor(217, 119, 87)
MONO = QFont("Cascadia Mono", 11)
if not MONO.exactMatch():
    MONO = QFont("Consolas", 11)
UI = QFont("Segoe UI", 10)

CODICE = [
    ("kw", "import "), ("", "pandas "), ("kw", "as "), ("", "pd\n"),
    ("", "\n"),
    ("kw", "def "), ("fn", "media_vendite"), ("", "(percorso):\n"),
    ("", "    dati = pd.read_csv(percorso)\n"),
    ("", "    totale = dati["), ("str", "\"importo\""), ("", "].sum()\n"),
    ("", "    mesi = dati["), ("str", "\"mese\""), ("", "].nunique()\n"),
    ("kw", "    return "), ("", "totale / mesi\n"),
    ("", "\n"),
    ("fn", "print"), ("", "(media_vendite("), ("str", "\"vendite_2026.csv\""), ("", "))\n"),
]
ERRORE = [
    "PS C:\\progetti\\report> python report.py",
    "Traceback (most recent call last):",
    "  File \"report.py\", line 9, in <module>",
    "    print(media_vendite(\"vendite_2026.csv\"))",
    "  File \"report.py\", line 5, in media_vendite",
    "    totale = dati[\"importo\"].sum()",
    "KeyError: 'importo'",
]


def desktop_codice() -> QImage:
    img = QImage(L, A, QImage.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, L, A)
    g.setColorAt(0, QColor(32, 58, 96))
    g.setColorAt(1, QColor(18, 28, 48))
    p.fillRect(img.rect(), g)
    # finestra dell'editor
    f = QRectF(70, 28, L - 140, 490)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(30, 31, 34))
    p.drawRoundedRect(f, 10, 10)
    p.setBrush(QColor(43, 45, 48))
    p.drawRoundedRect(QRectF(f.x(), f.y(), f.width(), 34), 10, 10)
    p.drawRect(QRectF(f.x(), f.y() + 20, f.width(), 14))
    for i, c in enumerate((QColor(255, 95, 86), QColor(255, 189, 46), QColor(39, 201, 63))):
        p.setBrush(c)
        p.drawEllipse(QPointF(f.x() + 20 + i * 20, f.y() + 17), 6, 6)
    p.setPen(QColor(170, 170, 175))
    p.setFont(UI)
    p.drawText(QRectF(f.x(), f.y(), f.width(), 34), Qt.AlignCenter, "report.py — Editor")
    # barra laterale dei file
    p.fillRect(QRectF(f.x(), f.y() + 34, 190, f.height() - 34), QColor(37, 38, 41))
    p.setPen(QColor(150, 150, 155))
    for i, nome in enumerate(("📁 report", "   report.py", "   vendite_2026.csv", "   README.md")):
        if i == 1:
            p.fillRect(QRectF(f.x() + 6, f.y() + 50 + i * 26 - 16, 178, 24), QColor(55, 57, 62))
        p.drawText(QPointF(f.x() + 16, f.y() + 56 + i * 26), nome)
    # codice
    colori = {"kw": QColor(204, 120, 50), "fn": QColor(255, 198, 109), "str": QColor(106, 171, 115),
              "": QColor(208, 208, 210)}
    p.setFont(MONO)
    x0, y0, alt = f.x() + 250, f.y() + 70, 22
    riga, x = 0, x0
    for n in range(10):
        p.setPen(QColor(90, 92, 98))
        p.drawText(QPointF(f.x() + 210, y0 + n * alt), f"{n + 1:>2}")
    for tipo, testo in CODICE:
        for i, pezzo in enumerate(testo.split("\n")):
            if i > 0:
                riga += 1
                x = x0
            p.setPen(colori[tipo])
            p.drawText(QPointF(x, y0 + riga * alt), pezzo)
            x += p.fontMetrics().horizontalAdvance(pezzo)
    # terminale con l'errore
    t = QRectF(f.x() + 190, f.bottom() - 205, f.width() - 190, 205)
    p.fillRect(t, QColor(24, 24, 27))
    p.fillRect(QRectF(t.x(), t.y(), t.width(), 1), QColor(60, 60, 66))
    p.setPen(QColor(150, 150, 155))
    p.setFont(UI)
    p.drawText(QPointF(t.x() + 18, t.y() + 24), "TERMINALE")
    p.setFont(MONO)
    for i, r in enumerate(ERRORE):
        p.setPen(QColor(241, 76, 76) if i == len(ERRORE) - 1 else
                 QColor(120, 200, 255) if i == 0 else QColor(200, 200, 204))
        p.drawText(QPointF(t.x() + 18, t.y() + 54 + i * 21), r)
    # barra delle applicazioni
    p.fillRect(QRectF(0, A - 48, L, 48), QColor(28, 30, 36, 245))
    for i in range(5):
        p.setBrush(QColor(255, 255, 255, 40 if i else 90))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(L / 2 - 120 + i * 50, A - 40, 34, 34), 7, 7)
    p.end()
    return img


def desktop_grafico() -> QImage:
    """Presentazione aperta su una slide con un grafico a barre (un'immagine, non testo da copiare)."""
    img = QImage(L, A, QImage.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, L, A)
    g.setColorAt(0, QColor(60, 44, 96))
    g.setColorAt(1, QColor(24, 22, 44))
    p.fillRect(img.rect(), g)
    f = QRectF(70, 28, L - 140, 490)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(243, 243, 245))
    p.drawRoundedRect(f, 10, 10)
    p.setBrush(QColor(196, 72, 44))
    p.drawRoundedRect(QRectF(f.x(), f.y(), f.width(), 34), 10, 10)
    p.drawRect(QRectF(f.x(), f.y() + 20, f.width(), 14))
    p.setPen(QColor("white"))
    p.setFont(UI)
    p.drawText(QRectF(f.x(), f.y(), f.width(), 34), Qt.AlignCenter, "Riunione trimestrale.pptx — Presentazione")
    # miniature delle slide
    p.fillRect(QRectF(f.x(), f.y() + 34, 170, f.height() - 34), QColor(228, 228, 232))
    for i in range(4):
        r = QRectF(f.x() + 22, f.y() + 52 + i * 104, 126, 72)
        p.setPen(QPen(QColor(196, 72, 44), 2) if i == 2 else QPen(QColor(200, 200, 205), 1))
        p.setBrush(QColor("white"))
        p.drawRoundedRect(r, 3, 3)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(210, 210, 215))
        p.drawRect(QRectF(r.x() + 10, r.y() + 10, 70, 6))
        if i == 2:
            for j, h in enumerate((20, 30, 26, 40)):
                p.setBrush(QColor(196, 72, 44, 160))
                p.drawRect(QRectF(r.x() + 20 + j * 22, r.bottom() - 10 - h, 12, h))
    # slide
    s = QRectF(f.x() + 210, f.y() + 60, f.width() - 250, f.height() - 90)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 25))
    p.drawRect(s.translated(3, 4))
    p.setBrush(QColor("white"))
    p.drawRect(s)
    p.setPen(QColor(40, 40, 46))
    p.setFont(QFont("Segoe UI Semibold", 20))
    p.drawText(QPointF(s.x() + 36, s.y() + 50), "Vendite per area · 2026")
    p.setPen(QColor(120, 120, 128))
    p.setFont(QFont("Segoe UI", 11))
    p.drawText(QPointF(s.x() + 36, s.y() + 76), "migliaia di euro, per trimestre")
    # grafico a barre raggruppate
    gr = ZONE["grafico"].adjusted(30, 20, -30, -34)
    serie = [("Nord", QColor(196, 72, 44)), ("Centro", QColor(232, 150, 90)), ("Sud", QColor(90, 120, 170))]
    valori = [(120, 80, 60), (135, 85, 58), (150, 70, 64), (190, 92, 75)]
    massimo = 200
    p.setPen(QPen(QColor(225, 225, 230), 1))
    for k in range(5):
        y = gr.bottom() - gr.height() * k / 4
        p.drawLine(QPointF(gr.x(), y), QPointF(gr.right(), y))
    p.setPen(QColor(140, 140, 148))
    p.setFont(QFont("Segoe UI", 9))
    larghezza_gruppo = gr.width() / len(valori)
    for i, gruppo in enumerate(valori):
        for j, v in enumerate(gruppo):
            h = gr.height() * v / massimo
            x = gr.x() + i * larghezza_gruppo + 22 + j * 30
            p.setPen(Qt.NoPen)
            p.setBrush(serie[j][1])
            p.drawRoundedRect(QRectF(x, gr.bottom() - h, 24, h), 3, 3)
        p.setPen(QColor(110, 110, 118))
        p.drawText(QRectF(gr.x() + i * larghezza_gruppo, gr.bottom() + 6, larghezza_gruppo, 18), Qt.AlignCenter,
                   f"T{i + 1}")
    for j, (nome, colore) in enumerate(serie):
        x = gr.right() - 230 + j * 80
        p.setPen(Qt.NoPen)
        p.setBrush(colore)
        p.drawRoundedRect(QRectF(x, gr.y() - 26, 12, 12), 2, 2)
        p.setPen(QColor(90, 90, 98))
        p.drawText(QPointF(x + 18, gr.y() - 15), nome)
    # riquadri con i numeri chiave a destra del grafico
    for k, (etichetta, numero) in enumerate((("Totale anno", "1.179 k€"), ("Area migliore", "Nord"),
                                             ("Trimestre migliore", "T4"))):
        r = QRectF(940, 170 + k * 96, 180, 80)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(247, 240, 236))
        p.drawRoundedRect(r, 8, 8)
        p.setPen(QColor(120, 120, 128))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(QPointF(r.x() + 16, r.y() + 28), etichetta)
        p.setPen(QColor(196, 72, 44))
        p.setFont(QFont("Segoe UI Semibold", 18))
        p.drawText(QPointF(r.x() + 16, r.y() + 62), numero)
    # barra delle applicazioni
    p.fillRect(QRectF(0, A - 48, L, 48), QColor(28, 30, 36, 245))
    for i in range(5):
        p.setBrush(QColor(255, 255, 255, 40 if i else 90))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(L / 2 - 120 + i * 50, A - 40, 34, 34), 7, 7)
    p.end()
    return img


# zona da cerchiare per ogni scena
ZONE = {
    "codice": QRectF(250, 352, 480, 150),   # attorno al traceback
    "grafico": QRectF(330, 160, 560, 300),  # attorno al grafico
}
DESKTOP = {"codice": desktop_codice, "grafico": desktop_grafico}
DOMANDE = {
    "codice": "Perché esce questo errore e come lo risolvo?",
    "grafico": "Riassumimi questo grafico in 3 punti",
}
ZONA = ZONE[SCENA]


def punto_cerchio(t: float) -> tuple[float, float]:
    """Tratto a mano libera attorno alla zona: ellisse un po' irregolare che si chiude oltre l'inizio."""
    c = ZONA.center()
    ang = -math.pi * 0.95 + t * math.tau * 1.06
    tremolio = 1 + 0.03 * math.sin(t * 23)
    return (c.x() + ZONA.width() / 2 * math.cos(ang) * tremolio,
            c.y() + ZONA.height() / 2 * math.sin(ang) * tremolio)


def cursore(p: QPainter, x: float, y: float, premuto: bool = False) -> None:
    forma = QPolygonF([QPointF(0, 0), QPointF(0, 19), QPointF(5, 14.5), QPointF(8.5, 22), QPointF(11.5, 20.5),
                       QPointF(8, 13.5), QPointF(14, 13.5)])
    p.save()
    p.translate(x, y)
    if premuto:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 70))
        p.drawEllipse(QPointF(0, 0), 16, 16)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(0, 0, 0), 1.3))
    p.setBrush(QColor(255, 255, 255))
    p.drawPolygon(forma)
    p.restore()


def didascalia(p: QPainter, numero: int, testo: str, alfa: float = 1.0) -> None:
    p.save()
    p.setOpacity(alfa)
    p.setRenderHint(QPainter.Antialiasing)
    f = QFont("Segoe UI Semibold", 17)
    p.setFont(f)
    larghezza = p.fontMetrics().horizontalAdvance(testo) + 96
    r = QRectF((L - larghezza) / 2, 24, larghezza, 54)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(15, 15, 18, 225))
    p.drawRoundedRect(r, 27, 27)
    p.setBrush(ARANCIO)
    p.drawEllipse(QPointF(r.x() + 30, r.center().y()), 15, 15)
    p.setPen(QColor("white"))
    p.setFont(QFont("Segoe UI Semibold", 13))
    p.drawText(QRectF(r.x() + 15, r.y(), 30, r.height()), Qt.AlignCenter, str(numero))
    p.setFont(f)
    p.drawText(QRectF(r.x() + 58, r.y(), r.width() - 70, r.height()), Qt.AlignVCenter, testo)
    p.restore()


def finale(t: float) -> QImage:
    img = QImage(L, A, QImage.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    g = QRadialGradient(L / 2, A / 2, L * 0.7)
    g.setColorAt(0, QColor(40, 41, 46))
    g.setColorAt(1, QColor(16, 16, 19))
    p.fillRect(img.rect(), g)
    entra = min(1.0, t / 0.6)
    p.setOpacity(entra)
    stella = icona_claude(72).toImage()
    p.drawImage(QPointF(L / 2 - 36, 170 - (1 - entra) * 20), stella)
    p.setPen(QColor("white"))
    p.setFont(QFont("Segoe UI Semibold", 46))
    p.drawText(QRectF(0, 260, L, 80), Qt.AlignCenter, "PCAnswerFinder")
    p.setPen(QColor(220, 220, 225))
    p.setFont(QFont("Segoe UI", 20))
    p.drawText(QRectF(0, 340, L, 44), Qt.AlignCenter, "Tieni premuto Win · cerchia · chiedi a Claude")
    p.setOpacity(min(1.0, max(0.0, (t - 0.5) / 0.6)))
    p.setPen(QColor(150, 150, 158))
    p.setFont(QFont("Segoe UI", 14))
    p.drawText(QRectF(0, 420, L, 30), Qt.AlignCenter, "Python · PySide6 · OCR di Windows · UI Automation · open source")
    p.setPen(ARANCIO)
    p.setFont(QFont("Segoe UI Semibold", 15))
    p.drawText(QRectF(0, 470, L, 30), Qt.AlignCenter, "github.com/AlessioLeo03/PCAnswerFinder")
    p.end()
    return img


def evento(s, tipo, x, y) -> None:
    pt = QPointF(x, y)
    stato = Qt.LeftButton if tipo != QEvent.MouseButtonRelease else Qt.NoButton
    QApplication.sendEvent(s, QMouseEvent(tipo, pt, s.mapToGlobal(pt), Qt.LeftButton, stato, Qt.NoModifier,
                                          QPointingDevice.primaryPointingDevice()))


def interpola(a, b, t):
    t = max(0.0, min(1.0, t))
    t = t * t * (3 - 2 * t)
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def fotogrammi():
    """Genera i fotogrammi uno alla volta (QImage 1280x720)."""
    base = DESKTOP[SCENA]()
    s = Schermata(Foto(QGuiApplication.primaryScreen(), base, (0, 0), 1.0), lambda x, y: None)
    s.setAttribute(Qt.WA_DontShowOnScreen)
    s.resize(L, A)
    s._ocr = "ok"
    s._lettore.pronto.disconnect()
    s.show()
    app.processEvents()

    def strato():
        app.processEvents()
        # lo schermo può avere ridimensionamento (es. 125 %): si riporta tutto a 1280x720
        img = s.grab().toImage().convertToFormat(QImage.Format_RGB32)
        if img.width() != L:
            img = img.scaled(L, A, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        img.setDevicePixelRatio(1.0)  # si disegna cursore e didascalie in pixel del video
        return img

    def con(img, mouse, numero=None, testo="", alfa=1.0, premuto=False):
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        if numero:
            didascalia(p, numero, testo, alfa)
        if mouse:
            cursore(p, *mouse, premuto=premuto)
        p.end()
        return img

    mouse = (900, 260)
    # 1) desktop con l'errore, poi "tieni premuto Win"
    for i in range(45):
        yield con(base.copy(), mouse, 1 if i > 12 else None, "Tieni premuto il tasto Win", min(1, (i - 12) / 8))
    # 2) lo schermo si ferma: buio + onda di luce
    for i in range(36):
        s._imposta_buio(min(1.0, i / 6))
        s._imposta_luce(-0.3 + 1.6 * i / 35)
        yield con(strato(), mouse, 1, "Tieni premuto il tasto Win")
    s._imposta_luce(-1.0)
    # 3) suggerimento d'uso
    s._mostra_suggerimento()
    # l'animazione vera andrebbe a tempo reale e litigherebbe con l'opacità impostata qui fotogramma per fotogramma
    s._anim_sugg.stop()
    s._anim_sugg.valueChanged.disconnect()
    for i in range(30):
        s._opacita.setOpacity(min(1.0, i / 8))
        # qui parla il suggerimento del programma: niente didascalia sopra
        yield con(strato(), interpola(mouse, punto_cerchio(0), i / 29))
    s._anim_sugg.stop()
    # 4) cerchio attorno all'errore
    inizio = punto_cerchio(0)
    evento(s, QEvent.MouseButtonPress, *inizio)
    passi = 60
    for i in range(1, passi + 1):
        pt = punto_cerchio(i / passi)
        evento(s, QEvent.MouseMove, *pt)
        yield con(strato(), pt, 2, "Cerchia quello che ti serve", min(1, i / 6), premuto=True)
    evento(s, QEvent.MouseButtonRelease, *punto_cerchio(1))
    s._avviso.hide()
    fine_cerchio = punto_cerchio(1)
    for i in range(18):
        yield con(strato(), fine_cerchio, 2, "Cerchia quello che ti serve")
    # 5) domanda
    domanda = DOMANDE[SCENA]
    campo = s._barra.campo
    pos_campo = campo.mapTo(s, campo.rect().center())
    verso_campo = (pos_campo.x() - 60, pos_campo.y() + 8)
    for i in range(14):
        yield con(strato(), interpola(fine_cerchio, verso_campo, i / 13), 3, "Scrivi la domanda", min(1, i / 6))
    for i in range(len(domanda) + 1):
        campo.setText(domanda[:i])
        for _ in range(2 if i < len(domanda) else 20):
            yield con(strato(), verso_campo, 3, "Scrivi la domanda")
    # 6) invio
    btn = s._barra.btn_invia
    centro = btn.mapTo(s, btn.rect().center())
    pos_btn = (centro.x() + 2, centro.y() + 4)
    for i in range(16):
        yield con(strato(), interpola(verso_campo, pos_btn, i / 15), 4, "Invio: la selezione va a Claude",
                  min(1, i / 6))
    for i in range(10):
        img = strato()
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, int(200 * (1 - i / 10))), 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(centro.x(), centro.y()), 22 + i * 3, 22 + i * 3)
        p.end()
        yield con(img, pos_btn, 4, "Invio: la selezione va a Claude", premuto=i < 4)
    # 7) chiusura con nome e link
    for i in range(int(FPS * 3.2)):
        yield finale(i / FPS)
    s.close()


def main() -> None:
    uscita = Path(_opzione("--uscita") or RADICE / "dist" / f"PCAnswerFinder-anteprima-{SCENA}.mp4").resolve()
    uscita.parent.mkdir(parents=True, exist_ok=True)
    if uscita.exists():
        uscita.unlink()

    formato = QVideoFrameFormat(QSize_(L, A), QVideoFrameFormat.Format_BGRX8888)
    formato.setStreamFrameRate(FPS)
    ingresso = QVideoFrameInput(formato)
    sessione = QMediaCaptureSession()
    sessione.setVideoFrameInput(ingresso)
    registratore = QMediaRecorder()
    sessione.setRecorder(registratore)
    mf = QMediaFormat(QMediaFormat.MPEG4)
    mf.setVideoCodec(QMediaFormat.VideoCodec.H264)
    registratore.setMediaFormat(mf)
    registratore.setQuality(QMediaRecorder.VeryHighQuality)
    registratore.setVideoResolution(L, A)
    registratore.setVideoFrameRate(FPS)
    registratore.setOutputLocation(QUrl.fromLocalFile(str(uscita)))

    generatore = fotogrammi()
    stato = {"n": 0, "finito": False}

    def invia_prossimo() -> None:
        # il disegno chiama processEvents: il segnale può arrivare mentre si prepara un fotogramma
        if stato.get("occupato"):
            return
        stato["occupato"] = True
        try:
            _invia()
        finally:
            stato["occupato"] = False

    def _invia() -> None:
        while not stato["finito"]:
            img = stato.pop("in_attesa", None)
            if img is None:
                try:
                    img = next(generatore)
                except StopIteration:
                    stato["finito"] = True
                    registratore.stop()
                    return
                if CAMPIONI and stato["n"] % PASSO == 0:
                    img.save(str(CAMPIONI / f"f{stato['n']:04d}.png"))
            frame = QVideoFrame(img)
            frame.setStartTime(stato["n"] * 1_000_000 // FPS)
            frame.setEndTime((stato["n"] + 1) * 1_000_000 // FPS)
            if not ingresso.sendVideoFrame(frame):
                stato["in_attesa"] = img  # coda piena: si riprende con readyToSendVideoFrame
                return
            stato["n"] += 1

    def cambiato(st) -> None:
        if st == QMediaRecorder.StoppedState and stato["finito"]:
            print(f"{uscita}  ({stato['n']} fotogrammi, {stato['n'] / FPS:.1f} s)")
            app.quit()

    def errore(_e, testo) -> None:
        print("Errore del registratore:", testo)
        app.exit(1)

    ingresso.readyToSendVideoFrame.connect(invia_prossimo)
    registratore.recorderStateChanged.connect(cambiato)
    registratore.errorOccurred.connect(errore)
    registratore.record()
    invia_prossimo()
    sys.exit(app.exec())


from PySide6.QtCore import QSize as QSize_  # noqa: E402

if __name__ == "__main__":
    main()
