"""Elemento dell'interfaccia (UI Automation) sotto un punto dello schermo."""
import ctypes
from ctypes import wintypes

from cerchia.gesti import Rett

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x2

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
_user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
_user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
_user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD]


def rett_elemento(x: int, y: int, da_ignorare: list[int]) -> Rett | None:
    """Rettangolo (pixel fisici del desktop) dell'elemento sotto (x, y).

    Le finestre in da_ignorare (gli strati di Cerchia e Chiedi) diventano trasparenti ai clic
    per il tempo della ricerca, così UI Automation vede cosa c'è sotto.
    """
    import uiautomation as auto  # importato tardi: dopo che Qt ha impostato la gestione DPI

    vecchi = []
    for h in da_ignorare:
        stile = _user32.GetWindowLongPtrW(h, GWL_EXSTYLE)
        vecchi.append((h, stile))
        _user32.SetWindowLongPtrW(h, GWL_EXSTYLE, stile | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        if not stile & WS_EX_LAYERED:
            _user32.SetLayeredWindowAttributes(h, 0, 255, LWA_ALPHA)
    try:
        el = auto.ControlFromPoint(x, y)
        if el is None:
            return None
        r = el.BoundingRectangle
        if r.width() <= 0 or r.height() <= 0:
            return None
        return Rett(r.left, r.top, r.width(), r.height())
    except Exception:
        return None
    finally:
        for h, stile in vecchi:
            _user32.SetWindowLongPtrW(h, GWL_EXSTYLE, stile)
