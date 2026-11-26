"""Scorciatoia per aprire lo strato: un tasto tenuto premuto oppure una combinazione scelta dall'utente.

Logica pura (nomi dei tasti, registrazione, avvisi) più il salvataggio con QSettings.
"""
from dataclasses import dataclass

from PySide6.QtCore import QSettings

VK_LWIN, VK_RWIN = 0x5B, 0x5C

# famiglie dei tasti di modifica: il lato (sinistro/destro) non conta nelle combinazioni
FAMIGLIE = {
    0x10: "maiusc", 0xA0: "maiusc", 0xA1: "maiusc",
    0x11: "ctrl", 0xA2: "ctrl", 0xA3: "ctrl",
    0x12: "alt", 0xA4: "alt", 0xA5: "alt",
    VK_LWIN: "win", VK_RWIN: "win",
}
ORDINE = ("win", "ctrl", "alt", "maiusc")
NOMI_FAMIGLIE = {"win": "Win", "ctrl": "Ctrl", "alt": "Alt", "maiusc": "Maiusc"}

NOMI = {
    VK_LWIN: "Win", VK_RWIN: "Win destro",
    0xA0: "Maiusc sinistro", 0xA1: "Maiusc destro", 0x10: "Maiusc",
    0xA2: "Ctrl sinistro", 0xA3: "Ctrl destro", 0x11: "Ctrl",
    0xA4: "Alt", 0xA5: "AltGr", 0x12: "Alt",
    0x08: "Backspace", 0x09: "Tab", 0x0D: "Invio", 0x13: "Pausa", 0x14: "Bloc Maiusc", 0x1B: "Esc",
    0x20: "Spazio", 0x21: "Pag su", 0x22: "Pag giù", 0x23: "Fine", 0x24: "Home",
    0x25: "←", 0x26: "↑", 0x27: "→", 0x28: "↓", 0x2C: "Stamp", 0x2D: "Ins", 0x2E: "Canc",
    0x5D: "Menu", 0x90: "Bloc Num", 0x91: "Bloc Scorr",
    0x6A: "Tn *", 0x6B: "Tn +", 0x6D: "Tn -", 0x6E: "Tn ,", 0x6F: "Tn /",
}
NOMI.update({0x30 + i: str(i) for i in range(10)})
NOMI.update({0x41 + i: chr(0x41 + i) for i in range(26)})
NOMI.update({0x60 + i: f"Tn {i}" for i in range(10)})
NOMI.update({0x70 + i: f"F{i + 1}" for i in range(24)})

# combinazioni che servono per lavorare: l'utente deve confermare se le sceglie
COMUNI = {
    (frozenset({"ctrl"}), ord(c)) for c in "ACVXZYSPFNOTW"
} | {
    (frozenset({"alt"}), 0x73), (frozenset({"alt"}), 0x09), (frozenset({"ctrl"}), 0x09),
    (frozenset({"ctrl", "maiusc"}), 0x1B), (frozenset({"win"}), ord("L")), (frozenset({"win"}), ord("D")),
    (frozenset({"win"}), ord("E")), (frozenset({"win"}), ord("R")), (frozenset({"win"}), ord("V")),
}
# tasti che servono per scrivere: tenerli premuti li ripete
DA_SCRITTURA = set(range(0x30, 0x3A)) | set(range(0x41, 0x5B)) | {0x08, 0x09, 0x0D, 0x20, 0x2E} | set(range(0x60, 0x70))


def famiglia(vk: int) -> str | None:
    return FAMIGLIE.get(vk)


def nome_tasto(vk: int) -> str:
    if vk in NOMI:
        return NOMI[vk]
    try:
        return _nome_da_windows(vk)
    except Exception:
        return f"Tasto {vk:#04x}"


def _nome_da_windows(vk: int) -> str:
    """Nome dato da Windows per i tasti non in elenco (es. è, ò, + sulla tastiera italiana)."""
    import ctypes
    user32 = ctypes.WinDLL("user32")
    scan = user32.MapVirtualKeyW(vk, 0)
    buf = ctypes.create_unicode_buffer(64)
    if scan and user32.GetKeyNameTextW(scan << 16, buf, 64):
        return buf.value.capitalize() if len(buf.value) > 1 else buf.value.upper()
    return f"Tasto {vk:#04x}"


@dataclass(frozen=True)
class Scorciatoia:
    tasto: int
    modificatori: frozenset[str] = frozenset()
    lunga: bool = False       # True = si tiene premuto "tasto" da solo
    soglia_ms: int = 500

    def nome(self) -> str:
        if self.lunga:
            return f"Tieni premuto {nome_tasto(self.tasto)}"
        mod = [NOMI_FAMIGLIE[f] for f in ORDINE if f in self.modificatori]
        return " + ".join(mod + [nome_tasto(self.tasto)])

    def tasti_lunghi(self) -> tuple[int, ...]:
        """Tasti che valgono come il tasto da tenere premuto (Win sinistro e destro sono lo stesso)."""
        if self.tasto in (VK_LWIN, VK_RWIN):
            return (VK_LWIN, VK_RWIN)
        return (self.tasto,)

    def avviso(self) -> str | None:
        """Motivo per cui la scorciatoia può dare fastidio, oppure None."""
        if self.lunga and self.tasto in DA_SCRITTURA:
            return f"Tenere premuto {nome_tasto(self.tasto)} serve anche a scrivere: potrebbe aprirsi mentre scrivi."
        if not self.lunga and (self.modificatori, self.tasto) in COMUNI:
            return f"{self.nome()} è una combinazione che si usa spesso: non farà più il suo lavoro normale."
        if not self.lunga and self.modificatori == frozenset({"maiusc"}):
            return f"{self.nome()} serve a scrivere: non funzionerà più per le maiuscole o i simboli."
        return None


PREDEFINITA = Scorciatoia(VK_LWIN, lunga=True, soglia_ms=500)


class Registratore:
    """Raccoglie i tasti premuti finché sono tutti rilasciati e ne ricava la scorciatoia.

    - modificatori tenuti + un tasto normale  -> combinazione (es. Ctrl + Maiusc + Q)
    - un solo tasto premuto e rilasciato      -> tieni premuto quel tasto
    - altro (es. solo Ctrl + Maiusc)          -> nessuna scorciatoia
    """

    def __init__(self) -> None:
        self._giu: set[int] = set()
        self._visti: list[int] = []
        self._combinazione: Scorciatoia | None = None

    def tasto(self, vk: int, giu: bool) -> Scorciatoia | None | bool:
        """Restituisce False finché la registrazione non è finita, poi la scorciatoia (o None)."""
        if giu:
            if vk not in self._giu:
                self._giu.add(vk)
                if vk not in self._visti:
                    self._visti.append(vk)
                if famiglia(vk) is None and self._combinazione is None:
                    mod = frozenset(f for f in (famiglia(v) for v in self._giu) if f)
                    if mod:
                        self._combinazione = Scorciatoia(vk, mod)
            return False
        if vk not in self._giu:  # rilascio di un tasto premuto prima di iniziare (es. Invio sul pulsante)
            return False
        self._giu.discard(vk)
        if self._giu:
            return False
        if self._combinazione is not None:
            return self._combinazione
        if len(self._visti) == 1:
            return Scorciatoia(self._visti[0], lunga=True)
        return None


def _impostazioni() -> QSettings:
    return QSettings("PCAnswerFinder", "PCAnswerFinder")


def carica(qs: QSettings | None = None) -> Scorciatoia:
    qs = qs or _impostazioni()
    try:
        tasto = int(qs.value("scorciatoia/tasto", PREDEFINITA.tasto))
        mod = str(qs.value("scorciatoia/modificatori", "") or "")
        lunga = str(qs.value("scorciatoia/lunga", "true")).lower() == "true"
        soglia = int(qs.value("scorciatoia/soglia_ms", PREDEFINITA.soglia_ms))
    except (TypeError, ValueError):
        return PREDEFINITA
    modificatori = frozenset(m for m in mod.split(",") if m in ORDINE)
    if not lunga and not modificatori:
        return PREDEFINITA
    return Scorciatoia(tasto, modificatori, lunga, max(200, min(2000, soglia)))


def salva(s: Scorciatoia, qs: QSettings | None = None) -> None:
    qs = qs or _impostazioni()
    qs.setValue("scorciatoia/tasto", s.tasto)
    qs.setValue("scorciatoia/modificatori", ",".join(f for f in ORDINE if f in s.modificatori))
    qs.setValue("scorciatoia/lunga", "true" if s.lunga else "false")
    qs.setValue("scorciatoia/soglia_ms", s.soglia_ms)
    qs.sync()
