"""Hook di tastiera a basso livello: riconosce la pressione lunga del tasto Win."""
import ctypes
import logging
from ctypes import wintypes

from PySide6.QtCore import QObject, Qt, QTimer, Signal

from cerchia import tastiera
from cerchia.stato_win import SOGLIA_MS, Stato, StatoWin

log = logging.getLogger(__name__)

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", wintypes.WPARAM)]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
_user32.SetWindowsHookExW.restype = wintypes.HHOOK
_user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
_user32.CallNextHookEx.restype = LRESULT
_user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
_kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
_kernel32.GetModuleHandleW.restype = wintypes.HMODULE
_kernel32.GetTickCount.restype = wintypes.DWORD


class TastoWin(QObject):
    avvia = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._stato = StatoWin()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.setInterval(SOGLIA_MS)
        self._timer.timeout.connect(self._scaduto)
        self._proc = HOOKPROC(self._callback)  # riferimento tenuto vivo
        self._hook = None

    def attiva(self) -> None:
        self._hook = _user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, _kernel32.GetModuleHandleW(None), 0)
        if not self._hook:
            raise OSError(ctypes.get_last_error(), "SetWindowsHookExW non riuscito")

    def disattiva(self) -> None:
        if self._hook:
            _user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    def _callback(self, n_code: int, w_param: int, l_param: int) -> int:
        try:
            if n_code == 0:
                k = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if k.dwExtraInfo != tastiera.MARCA:
                    giu = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                    prima = self._stato.stato
                    esito = self._stato.tasto(k.vkCode, giu, k.time)
                    if prima is not Stato.ATTESA and self._stato.stato is Stato.ATTESA:
                        self._timer.start()
                    if esito.reinvia:
                        eventi = list(esito.reinvia)
                        QTimer.singleShot(0, lambda: tastiera.invia(eventi))
                    if esito.avvia:
                        QTimer.singleShot(0, self.avvia.emit)
                    if esito.blocca:
                        return 1
        except Exception:  # l'hook non deve mai bloccare la tastiera
            log.exception("errore nel hook di tastiera")
        return _user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _scaduto(self) -> None:
        ora = _kernel32.GetTickCount()
        if self._stato.tempo(ora):
            self.avvia.emit()
        elif self._stato.stato is Stato.ATTESA:  # timer scattato un po' in anticipo
            self._timer.start(self._stato.rimanente_ms(ora))
