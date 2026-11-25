"""Invio di tasti simulati con SendInput, marcati per essere riconosciuti dall'hook."""
import ctypes
from ctypes import wintypes

MARCA = 0x43434843  # valore in dwExtraInfo dei tasti inviati da Cerchia e Chiedi

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
# Tasti che Windows considera "estesi"
ESTESI = {0x5B, 0x5C, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E}

ULONG_PTR = wintypes.WPARAM


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _UNIONE(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _UNIONE)]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
_user32.SendInput.restype = wintypes.UINT


def invia(eventi: list[tuple[int, bool]]) -> None:
    """eventi: lista di (codice VK, True = premuto / False = rilasciato)."""
    if not eventi:
        return
    arr = (INPUT * len(eventi))()
    for i, (vk, giu) in enumerate(eventi):
        flag = 0 if giu else KEYEVENTF_KEYUP
        if vk in ESTESI:
            flag |= KEYEVENTF_EXTENDEDKEY
        arr[i].type = INPUT_KEYBOARD
        arr[i].u.ki = KEYBDINPUT(vk, 0, flag, 0, MARCA)
    _user32.SendInput(len(eventi), arr, ctypes.sizeof(INPUT))


def combinazione(*vks: int) -> None:
    """Preme i tasti nell'ordine dato e li rilascia in ordine inverso (es. Ctrl+V)."""
    invia([(v, True) for v in vks] + [(v, False) for v in reversed(vks)])
