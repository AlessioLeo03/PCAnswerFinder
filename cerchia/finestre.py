"""Finestre di Windows: portare una finestra in primo piano."""
import ctypes
import time
from ctypes import wintypes

from PySide6.QtWidgets import QApplication

SW_RESTORE = 9

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.BringWindowToTop.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
_kernel32.GetCurrentThreadId.restype = wintypes.DWORD


def _aspetta(ms: int) -> None:
    fine = time.monotonic() + ms / 1000
    while time.monotonic() < fine:
        QApplication.processEvents()
        time.sleep(0.02)


def porta_in_primo_piano(hwnd: int) -> bool:
    """Porta la finestra davanti a tutte e le da il focus; True se ci riesce entro circa 1 secondo."""
    if _user32.IsIconic(hwnd):
        _user32.ShowWindow(hwnd, SW_RESTORE)
    davanti = _user32.GetForegroundWindow()
    t_davanti = _user32.GetWindowThreadProcessId(davanti, None) if davanti else 0
    t_mio = _kernel32.GetCurrentThreadId()
    collegato = bool(t_davanti) and t_davanti != t_mio and bool(_user32.AttachThreadInput(t_mio, t_davanti, True))
    try:
        _user32.BringWindowToTop(hwnd)
        _user32.SetForegroundWindow(hwnd)
    finally:
        if collegato:
            _user32.AttachThreadInput(t_mio, t_davanti, False)
    for _ in range(20):
        if _user32.GetForegroundWindow() == hwnd:
            return True
        _aspetta(50)
    return False
