"""Crea pacchetto/icona.ico (cerchio arancione, come l'icona nell'area di notifica)."""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen

app = QGuiApplication(sys.argv)
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
p.setPen(QPen(QColor(217, 119, 87), 30))
p.drawEllipse(36, 36, 184, 184)
p.end()
destinazione = Path(__file__).with_name("icona.ico")
if not img.save(str(destinazione), "ICO"):
    sys.exit("Impossibile salvare l'icona")
print(destinazione)
