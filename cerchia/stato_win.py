"""Macchina a stati della pressione del tasto Win (logica pura, senza Windows)."""
from dataclasses import dataclass, field
from enum import Enum, auto

VK_LWIN = 0x5B
VK_RWIN = 0x5C
SOGLIA_MS = 500


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


def _e_win(vk: int) -> bool:
    return vk in (VK_LWIN, VK_RWIN)


class StatoWin:
    def __init__(self, soglia_ms: int = SOGLIA_MS) -> None:
        self.soglia_ms = soglia_ms
        self.stato = Stato.RIPOSO
        self._vk_win = VK_LWIN
        self._inizio_ms = 0

    def tasto(self, vk: int, giu: bool, ora_ms: int) -> Esito:
        if self.stato is Stato.RIPOSO:
            if _e_win(vk) and giu:
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
