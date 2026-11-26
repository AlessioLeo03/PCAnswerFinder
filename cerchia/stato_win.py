"""Macchine a stati della scorciatoia (logica pura, senza Windows).

- StatoWin: un tasto tenuto premuto (di serie Win). Pressione breve e combinazioni restano normali.
- StatoCombinazione: una combinazione come Ctrl + Maiusc + Q.
"""
from dataclasses import dataclass, field
from enum import Enum, auto

VK_LWIN = 0x5B
VK_RWIN = 0x5C
SOGLIA_MS = 500
# tasto senza funzione: inviato tra pressione e rilascio di Win/Alt perché non si aprano Start o i menu
VK_MASCHERA = 0xE8

_FAMIGLIE = {
    0x10: "maiusc", 0xA0: "maiusc", 0xA1: "maiusc",
    0x11: "ctrl", 0xA2: "ctrl", 0xA3: "ctrl",
    0x12: "alt", 0xA4: "alt", 0xA5: "alt",
    VK_LWIN: "win", VK_RWIN: "win",
}


class Stato(Enum):
    RIPOSO = auto()
    ATTESA = auto()
    AVVIATO = auto()
    COMBINAZIONE = auto()


@dataclass
class Esito:
    blocca: bool
    reinvia: list[tuple[int, bool]] = field(default_factory=list)  # (vk, giu)
    avvia: bool = False


class StatoWin:
    """Pressione lunga di un tasto (di serie Win sinistro o destro)."""

    def __init__(self, soglia_ms: int = SOGLIA_MS, tasti: tuple[int, ...] = (VK_LWIN, VK_RWIN)) -> None:
        self.soglia_ms = soglia_ms
        self.tasti = tasti
        self.stato = Stato.RIPOSO
        self._vk_win = tasti[0]
        self._inizio_ms = 0

    def tasto(self, vk: int, giu: bool, ora_ms: int) -> Esito:
        if self.stato is Stato.RIPOSO:
            if vk in self.tasti and giu:
                self.stato = Stato.ATTESA
                self._vk_win = vk
                self._inizio_ms = ora_ms
                return Esito(blocca=True)
            return Esito(blocca=False)

        if self.stato is Stato.ATTESA:
            if vk == self._vk_win:
                if giu:  # ripetizione automatica del tasto tenuto premuto
                    return Esito(blocca=True, avvia=self.tempo(ora_ms))
                self.stato = Stato.RIPOSO
                return Esito(blocca=True, reinvia=[(vk, True), (vk, False)])
            if giu:
                self.stato = Stato.COMBINAZIONE
                return Esito(blocca=True, reinvia=[(self._vk_win, True), (vk, True)])
            return Esito(blocca=False)

        if self.stato is Stato.COMBINAZIONE:
            if vk == self._vk_win and not giu:
                self.stato = Stato.RIPOSO
            return Esito(blocca=False)

        # Stato.AVVIATO
        if vk == self._vk_win:
            if not giu:
                self.stato = Stato.RIPOSO
            return Esito(blocca=True)
        return Esito(blocca=False)

    def rimanente_ms(self, ora_ms: int) -> int:
        """Millisecondi che mancano alla soglia (almeno 10)."""
        return max(10, self.soglia_ms - (ora_ms - self._inizio_ms))

    def tempo(self, ora_ms: int) -> bool:
        """Da chiamare con un timer: True se la pressione è appena diventata lunga."""
        if self.stato is Stato.ATTESA and ora_ms - self._inizio_ms >= self.soglia_ms:
            self.stato = Stato.AVVIATO
            return True
        return False


class StatoCombinazione:
    """Combinazione esatta: i modificatori indicati (né più né meno) e poi il tasto principale.

    Il tasto principale viene bloccato (giù, ripetizioni e su), così l'app sotto non lo riceve.
    Se nella combinazione ci sono Win o Alt, al momento dello scatto si invia VK_MASCHERA:
    al rilascio Windows non apre Start e le finestre non attivano la barra dei menu.
    """

    def __init__(self, modificatori: frozenset[str], tasto: int) -> None:
        self.modificatori = modificatori
        self.principale = tasto
        self.stato = Stato.RIPOSO
        self._giu: set[int] = set()

    def _famiglie_giu(self) -> frozenset[str]:
        return frozenset(f for f in (_FAMIGLIE.get(v) for v in self._giu) if f)

    def tasto(self, vk: int, giu: bool, ora_ms: int) -> Esito:
        if vk in _FAMIGLIE:
            if giu:
                self._giu.add(vk)
            else:
                self._giu.discard(vk)
            return Esito(blocca=False)
        if vk != self.principale:
            return Esito(blocca=False)
        if self.stato is Stato.AVVIATO:  # ripetizioni e rilascio del tasto che ha fatto scattare
            if not giu:
                self.stato = Stato.RIPOSO
            return Esito(blocca=True)
        if giu and self._famiglie_giu() == self.modificatori:
            self.stato = Stato.AVVIATO
            maschera = [(VK_MASCHERA, True), (VK_MASCHERA, False)] if self.modificatori & {"win", "alt"} else []
            return Esito(blocca=True, reinvia=maschera, avvia=True)
        return Esito(blocca=False)

    def tempo(self, ora_ms: int) -> bool:
        return False

    def rimanente_ms(self, ora_ms: int) -> int:
        return 10
