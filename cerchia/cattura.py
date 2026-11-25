"""Foto di tutti gli schermi in pixel fisici e ritagli PNG (solo in memoria)."""
import ctypes
import math
from ctypes import wintypes
from dataclasses import dataclass

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRect
from PySide6.QtGui import QGuiApplication, QImage, QScreen

from cerchia.gesti import Rett


@dataclass
class Foto:
    schermo: QScreen
    immagine: QImage          # pixel fisici, devicePixelRatio = 1
    origine: tuple[int, int]  # angolo in alto a sinistra, pixel fisici del desktop
    dpr: float


class _MONITORINFOEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD), ("szDevice", wintypes.WCHAR * 32)]


_MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                      ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)


def _origini_fisiche() -> dict[str, tuple[int, int]]:
    r"""Nome del monitor (es. \.DISPLAY1) -> angolo in pixel fisici."""
    risultato: dict[str, tuple[int, int]] = {}

    def cb(hmon, _hdc, _rect, _lparam):
        info = _MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        if ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            risultato[info.szDevice] = (info.rcMonitor.left, info.rcMonitor.top)
        return True

    ctypes.windll.user32.EnumDisplayMonitors(None, None, _MONITORENUMPROC(cb), 0)
    return risultato


def fotografa() -> list[Foto]:
    origini = _origini_fisiche()
    foto = []
    for schermo in QGuiApplication.screens():
        img = schermo.grabWindow(0).toImage()
        img.setDevicePixelRatio(1.0)
        g = schermo.geometry()
        origine = origini.get(schermo.name(), (g.x(), g.y()))
        foto.append(Foto(schermo, img, origine, schermo.devicePixelRatio()))
    return foto


def png_da_immagine(img: QImage) -> bytes:
    dati = QByteArray()
    buf = QBuffer(dati)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    return bytes(dati.data())


def ritaglio_png(img: QImage, r: Rett) -> bytes:
    x0, y0 = math.floor(r.x), math.floor(r.y)
    x1, y1 = math.ceil(r.x + r.w), math.ceil(r.y + r.h)
    area = QRect(x0, y0, x1 - x0, y1 - y0).intersected(img.rect())
    if area.isEmpty():
        return b""
    return png_da_immagine(img.copy(area))
