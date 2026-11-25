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


PASSI = [
    "Tieni premuto il tasto Win",
    "Cerchia quello che ti serve",
    "Scrivi la domanda",
    "Premi Invio",
    "Claude risponde",
]
PANNELLO = 300                       # larghezza del pannello delle istruzioni a sinistra
SCENA_R = QRectF(PANNELLO, 90, 960, 540)  # dove va lo schermo (1280x720 rimpicciolito al 75 %)

RISPOSTE = {
    "grafico": (
        "Ecco il grafico in 3 punti:\n\n"
        "1. Il Nord guida e cresce ogni trimestre: da 120 a 190 k€ (+58 %).\n\n"
        "2. Centro e Sud restano stabili, tra 58 e 92 k€, senza una crescita netta.\n\n"
        "3. T4 è il trimestre migliore per tutte e tre le aree; il totale dell'anno è 1.179 k€."
    ),
    "codice": (
        "KeyError: 'importo' vuol dire che nel CSV non c'è una colonna che si chiama esattamente \"importo\".\n\n"
        "1. Controlla i nomi delle colonne: print(dati.columns)\n\n"
        "2. Spesso ci sono spazi o maiuscole diverse (\"Importo \"): normalizzali con\n"
        "    dati.columns = dati.columns.str.strip().str.lower()\n\n"
        "3. Poi rilancia: dati[\"importo\"] funzionerà."
    ),
}


def tasto_win(p: QPainter, centro: QPointF, premuto: float, progresso: float) -> None:
    """Tasto Win disegnato: premuto (0-1) lo abbassa, progresso (0-1) riempie l'anello del mezzo secondo."""
    lato = 92
    giu = 6 * premuto
    r = QRectF(centro.x() - lato / 2, centro.y() - lato / 2 + giu, lato, lato)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 120))
    p.drawRoundedRect(QRectF(r.x(), centro.y() - lato / 2 + 8, lato, lato), 16, 16)
    p.setBrush(QColor(70 - 15 * premuto, 72 - 15 * premuto, 80 - 15 * premuto))
    p.drawRoundedRect(r, 16, 16)
    p.setBrush(QColor(92 - 15 * premuto, 95 - 15 * premuto, 104 - 15 * premuto))
    p.drawRoundedRect(r.adjusted(6, 5, -6, -9), 12, 12)
    # logo di Windows: quattro quadrati
    q, gap = 15, 3
    c = r.adjusted(6, 5, -6, -9).center()
    p.setBrush(QColor(120, 190, 255) if premuto > 0.5 else QColor(230, 232, 238))
    for dx in (-1, 1):
        for dy in (-1, 1):
            p.drawRect(QRectF(c.x() + (gap / 2 if dx > 0 else -gap / 2 - q),
                              c.y() + (gap / 2 if dy > 0 else -gap / 2 - q), q, q))
    if progresso > 0:
        p.setPen(QPen(ARANCIO, 5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        anello = r.adjusted(-14, -14 - giu, 14, 14 - giu)
        p.drawArc(anello, 90 * 16, int(-360 * 16 * min(1.0, progresso)))
    p.restore()


def pannello(p: QPainter, attivo: int, extra: dict) -> None:
    """Colonna a sinistra: nome, i passi con quello attivo evidenziato, il tasto Win nel primo passo."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(0, 0, PANNELLO, A), QColor(20, 20, 24))
    p.drawImage(QPointF(34, 46), icona_claude(30).toImage())
    p.setPen(QColor("white"))
    p.setFont(QFont("Segoe UI Semibold", 17))
    p.drawText(QPointF(74, 70), "PCAnswerFinder")
    p.setPen(QColor(150, 150, 158))
    p.setFont(QFont("Segoe UI", 10))
    p.drawText(QPointF(36, 100), "Cerchia e chiedi, su PC, con Claude")
    y = 150
    for i, testo in enumerate(PASSI, start=1):
        fatto, ora = i < attivo, i == attivo
        p.setPen(Qt.NoPen)
        if ora:
            p.setBrush(QColor(255, 255, 255, 14))
            p.drawRoundedRect(QRectF(20, y - 24, PANNELLO - 40, 48), 12, 12)
        p.setBrush(ARANCIO if ora else QColor(60, 62, 68) if not fatto else QColor(70, 120, 85))
        p.drawEllipse(QPointF(48, y), 14, 14)
        p.setPen(QColor("white"))
        p.setFont(QFont("Segoe UI Semibold", 11))
        p.drawText(QRectF(34, y - 14, 28, 28), Qt.AlignCenter, "✓" if fatto else str(i))
        p.setPen(QColor("white") if ora else QColor(170, 170, 178) if fatto else QColor(110, 110, 118))
        p.setFont(QFont("Segoe UI Semibold" if ora else "Segoe UI", 13))
        p.drawText(QPointF(74, y + 6), testo)
        y += 62
    if attivo == 1:
        tasto_win(p, QPointF(PANNELLO / 2, 535), extra.get("premuto", 0.0), extra.get("progresso", 0.0))
        p.setPen(QColor(170, 170, 178))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRectF(0, 600, PANNELLO, 22), Qt.AlignCenter, "circa mezzo secondo")
    p.setPen(QColor(90, 90, 98))
    p.setFont(QFont("Segoe UI", 8))
    p.drawText(QRectF(0, A - 34, PANNELLO, 20), Qt.AlignCenter, "Demo ricostruita · dati di esempio")
    p.restore()


def componi(scena: QImage, attivo: int, extra: dict | None = None) -> QImage:
    """Fotogramma finale: pannello a sinistra e lo schermo rimpicciolito a destra."""
    img = QImage(L, A, QImage.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    g = QLinearGradient(PANNELLO, 0, L, A)
    g.setColorAt(0, QColor(34, 34, 40))
    g.setColorAt(1, QColor(22, 22, 27))
    p.fillRect(img.rect(), g)
    pannello(p, attivo, extra or {})
    ombra = SCENA_R.adjusted(-2, 4, 2, 10)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 110))
    p.drawRoundedRect(ombra, 14, 14)
    percorso = QPainterPath()
    percorso.addRoundedRect(SCENA_R, 12, 12)
    p.setClipPath(percorso)
    p.drawImage(SCENA_R, scena)
    p.end()
    return img


def chat_claude_finestra(base: QImage, ritaglio: QImage, domanda: str, risposta: str, mostrati: int,
                         entrata: float) -> QImage:
    """Finestra di chat di esempio con la selezione inviata e la risposta che compare man mano."""
    img = base.copy()
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    f = QRectF(170, 30 + (1 - entrata) * 30, 940, 630)
    p.setOpacity(entrata)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 120))
    p.drawRoundedRect(f.adjusted(-3, 6, 3, 14), 14, 14)
    p.setBrush(QColor(38, 38, 36))
    p.drawRoundedRect(f, 12, 12)
    p.setBrush(QColor(30, 30, 29))
    p.drawRoundedRect(QRectF(f.x(), f.y(), f.width(), 40), 12, 12)
    p.drawRect(QRectF(f.x(), f.y() + 26, f.width(), 14))
    p.drawImage(QPointF(f.x() + 16, f.y() + 10), icona_claude(20).toImage())
    p.setPen(QColor(230, 230, 228))
    p.setFont(QFont("Segoe UI Semibold", 11))
    p.drawText(QPointF(f.x() + 44, f.y() + 26), "Claude · chat nuova")
    # messaggio dell'utente: immagine + domanda, a destra
    p.setFont(QFont("Segoe UI", 13))
    larghezza = int(min(460, max(300, p.fontMetrics().horizontalAdvance(domanda) + 8)))
    alt = ritaglio.height() * larghezza / ritaglio.width()
    m = QRectF(f.right() - larghezza - 40, f.y() + 62, larghezza + 24, alt + 64)
    p.setBrush(QColor(55, 55, 52))
    p.drawRoundedRect(m, 14, 14)
    p.drawImage(QRectF(m.x() + 12, m.y() + 12, larghezza, alt), ritaglio)
    p.setPen(QColor(240, 240, 238))
    p.setFont(QFont("Segoe UI", 12))
    p.drawText(QRectF(m.x() + 14, m.y() + alt + 20, larghezza, 30), Qt.AlignLeft | Qt.AlignVCenter, domanda)
    # risposta
    y0 = m.bottom() + 26
    p.drawImage(QPointF(f.x() + 36, y0 + 2), icona_claude(24).toImage())
    testo = risposta[:mostrati]
    if mostrati < len(risposta):
        testo += " ▍"
    p.setPen(QColor(236, 236, 232))
    p.setFont(QFont("Segoe UI", 13))
    p.drawText(QRectF(f.x() + 76, y0, f.width() - 130, f.bottom() - y0 - 20), Qt.TextWordWrap | Qt.AlignTop, testo)
    p.end()
    return img


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
        img.setDevicePixelRatio(1.0)  # si disegna il cursore in pixel dello schermo
        return img

    def con(img, mouse, premuto=False):
        if mouse:
            p = QPainter(img)
            p.setRenderHint(QPainter.Antialiasing)
            cursore(p, *mouse, premuto=premuto)
            p.end()
        return img

    mouse = (900, 260)
    # 1) desktop, poi il tasto Win si abbassa e l'anello si riempie
    for i in range(24):
        yield componi(con(base.copy(), mouse), 1)
    for i in range(24):
        premuto = min(1.0, i / 4)
        yield componi(con(base.copy(), mouse), 1, {"premuto": premuto, "progresso": i / 18})
    # 2) lo schermo si ferma: buio + onda di luce (il tasto si rilascia)
    for i in range(36):
        s._imposta_buio(min(1.0, i / 6))
        s._imposta_luce(-0.3 + 1.6 * i / 35)
        yield componi(con(strato(), mouse), 1, {"premuto": max(0.0, 1 - i / 6), "progresso": 1.0 if i < 10 else 0})
    s._imposta_luce(-1.0)
    # 3) suggerimento d'uso del programma
    s._mostra_suggerimento()
    # l'animazione vera andrebbe a tempo reale e litigherebbe con l'opacità impostata qui fotogramma per fotogramma
    s._anim_sugg.stop()
    s._anim_sugg.valueChanged.disconnect()
    for i in range(30):
        s._opacita.setOpacity(min(1.0, i / 8))
        yield componi(con(strato(), interpola(mouse, punto_cerchio(0), i / 29)), 2)
    # 4) cerchio
    evento(s, QEvent.MouseButtonPress, *punto_cerchio(0))
    passi = 60
    for i in range(1, passi + 1):
        pt = punto_cerchio(i / passi)
        evento(s, QEvent.MouseMove, *pt)
        yield componi(con(strato(), pt, premuto=True), 2)
    evento(s, QEvent.MouseButtonRelease, *punto_cerchio(1))
    s._avviso.hide()
    fine_cerchio = punto_cerchio(1)
    for i in range(16):
        yield componi(con(strato(), fine_cerchio), 2)
    # 5) domanda
    domanda = DOMANDE[SCENA]
    campo = s._barra.campo
    pos_campo = campo.mapTo(s, campo.rect().center())
    verso_campo = (pos_campo.x() - 60, pos_campo.y() + 8)
    for i in range(12):
        yield componi(con(strato(), interpola(fine_cerchio, verso_campo, i / 11)), 3)
    for i in range(len(domanda) + 1):
        campo.setText(domanda[:i])
        for _ in range(2 if i < len(domanda) else 14):
            yield componi(con(strato(), verso_campo), 3)
    # 6) invio
    btn = s._barra.btn_invia
    centro = btn.mapTo(s, btn.rect().center())
    pos_btn = (centro.x() + 2, centro.y() + 4)
    for i in range(14):
        yield componi(con(strato(), interpola(verso_campo, pos_btn, i / 13)), 4)
    for i in range(10):
        img = strato()
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, int(200 * (1 - i / 10))), 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(centro.x(), centro.y()), 22 + i * 3, 22 + i * 3)
        p.end()
        yield componi(con(img, pos_btn, premuto=i < 4), 4)
    # 7) la chat si apre con la selezione e la risposta compare man mano
    riquadro = s._riquadro
    ritaglio = base.copy(int(riquadro.x), int(riquadro.y), int(riquadro.w), int(riquadro.h))
    s.close()
    risposta = RISPOSTE[SCENA]
    for i in range(14):
        yield componi(chat_claude_finestra(base, ritaglio, domanda, risposta, 0, i / 13), 5)
    for i in range(12):  # "sta pensando"
        yield componi(chat_claude_finestra(base, ritaglio, domanda, risposta, 0, 1.0), 5)
    mostrati = 0
    while mostrati < len(risposta):
        mostrati = min(len(risposta), mostrati + 4)
        yield componi(chat_claude_finestra(base, ritaglio, domanda, risposta, mostrati, 1.0), 5)
    for i in range(int(FPS * 2.2)):
        yield componi(chat_claude_finestra(base, ritaglio, domanda, risposta, mostrati, 1.0), 5)
    # 8) chiusura con nome e link
    for i in range(int(FPS * 3)):
        yield finale(i / FPS)


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
