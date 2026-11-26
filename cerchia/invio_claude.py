"""Invio della selezione all'app desktop di Claude: chat nuova, incolla, invia."""
import ctypes
import os
import subprocess
import time
from collections.abc import Callable
from ctypes import wintypes

from PySide6.QtWidgets import QApplication

from cerchia import appunti, impostazioni, tastiera
from cerchia.destinazione import APERTA, CERCA, Destinazione
from cerchia.finestre import porta_in_primo_piano

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_V = 0x56

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [_ENUMPROC, wintypes.LPARAM]
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                 ctypes.POINTER(wintypes.DWORD)]
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def _aspetta(ms: int) -> None:
    fine = time.monotonic() + ms / 1000
    while time.monotonic() < fine:
        QApplication.processEvents()
        time.sleep(0.02)


def _percorso_processo(hwnd: int) -> str:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wintypes.DWORD(1024)
        if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return buf.value
        return ""
    finally:
        _kernel32.CloseHandle(h)


def e_app_claude(percorso: str) -> bool:
    """True se il percorso e' il claude.exe dell'app desktop di Claude (non quello di Claude Code).

    Riconosce sia l'installer classico (...\\AnthropicClaude\\...) sia la versione
    del Microsoft Store (...\\WindowsApps\\Claude_<versione>_<arch>__<id>\\app\\Claude.exe).
    """
    p = percorso.lower()
    if not p.endswith("\\claude.exe"):
        return False
    return "\\anthropicclaude\\" in p or ("\\windowsapps\\claude_" in p and "\\app\\" in p)


def trova_finestra() -> int | None:
    """Finestra principale dell'app desktop di Claude (esclude il claude.exe di Claude Code)."""
    trovate: list[int] = []

    @_ENUMPROC
    def cb(hwnd, _lparam):
        if _user32.IsWindowVisible(hwnd) and _user32.GetWindowTextLengthW(hwnd) > 0:
            if e_app_claude(_percorso_processo(hwnd)):
                trovate.append(hwnd)
                return False
        return True

    _user32.EnumWindows(cb, 0)
    return trovate[0] if trovate else None


def _attiva(hwnd: int) -> bool:
    return porta_in_primo_piano(hwnd)


def _apri_chat_nuova() -> bool:
    metodo, valore = impostazioni.CHAT_NUOVA
    if metodo == "tasti":
        tastiera.combinazione(*valore)
        return True
    if metodo == "link":
        os.startfile(valore)
        return True
    return False


def _vai_alla_chat(dest: Destinazione, avvisa: Callable[[str], None]) -> None:
    """Porta l'app di Claude sulla chat scelta; l'app deve già essere in primo piano."""
    if dest.modo == APERTA:
        return
    if dest.modo == CERCA:
        tastiera.combinazione(*impostazioni.CERCA_CHAT)
        _aspetta(impostazioni.ATTESA_RICERCA_MS)
        appunti.metti_testo(dest.titolo.strip())
        _aspetta(100)
        tastiera.combinazione(VK_CONTROL, VK_V)
        _aspetta(impostazioni.ATTESA_RISULTATI_MS)
        tastiera.combinazione(VK_RETURN)
        _aspetta(impostazioni.ATTESA_CHAT_NUOVA_MS)
        return
    if _apri_chat_nuova():
        _aspetta(impostazioni.ATTESA_CHAT_NUOVA_MS)
    else:
        avvisa("Chat nuova non disponibile: uso la chat aperta.")


def invia(png: bytes, testo: str, avvisa: Callable[[str], None],
          dest: Destinazione = Destinazione()) -> None:
    salvati = appunti.salva()
    hwnd = trova_finestra()
    if hwnd is None:
        programma = os.path.expandvars(impostazioni.CLAUDE_EXE)
        try:
            if os.path.exists(programma):
                subprocess.Popen([programma])
            else:
                # Versione del Microsoft Store: si avvia dal suo AppUserModelID
                subprocess.Popen(["explorer.exe", impostazioni.CLAUDE_STORE_APPID])
        except OSError:
            pass
        fine = time.monotonic() + 20
        while hwnd is None and time.monotonic() < fine:
            _aspetta(500)
            hwnd = trova_finestra()
        if hwnd is None:
            appunti.metti_immagine(png)
            avvisa("Claude non si è aperto: incolla con Ctrl+V.")
            return
        _aspetta(impostazioni.ATTESA_AVVIO_MS)

    try:
        if not _attiva(hwnd):
            appunti.metti_immagine(png)
            avvisa("Non riesco a portare Claude in primo piano: incolla con Ctrl+V.")
            return
        _aspetta(300)

        _vai_alla_chat(dest, avvisa)

        appunti.metti_immagine(png)
        _aspetta(100)
        tastiera.combinazione(VK_CONTROL, VK_V)
        _aspetta(impostazioni.ATTESA_CARICAMENTO_MS)

        appunti.metti_testo(testo)
        _aspetta(100)
        tastiera.combinazione(VK_CONTROL, VK_V)
        _aspetta(200)
        tastiera.combinazione(VK_RETURN)

        _aspetta(300)
        appunti.ripristina(salvati)
    except Exception as e:
        appunti.ripristina(salvati)
        avvisa(f"Errore durante l'invio: {e}")
