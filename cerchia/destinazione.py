"""Dove mandare la selezione nell'app di Claude: chat nuova, chat aperta o chat cercata per titolo."""
from dataclasses import dataclass

from PySide6.QtCore import QSettings

NUOVA = "nuova"
APERTA = "aperta"
CERCA = "cerca"

# (valore, etichetta nel menu della barra)
VOCI = [
    (NUOVA, "Chat nuova"),
    (APERTA, "Chat aperta"),
    (CERCA, "Cerca chat…"),
]


@dataclass(frozen=True)
class Destinazione:
    modo: str = NUOVA
    titolo: str = ""

    def valida(self) -> bool:
        return self.modo != CERCA or bool(self.titolo.strip())


def _impostazioni() -> QSettings:
    return QSettings("CerchiaEChiedi", "CerchiaEChiedi")


def carica(qs: QSettings | None = None) -> Destinazione:
    """Ultima destinazione scelta (chat nuova se non c'è niente di salvato)."""
    qs = qs or _impostazioni()
    modo = str(qs.value("destinazione/modo", NUOVA))
    if modo not in (NUOVA, APERTA, CERCA):
        modo = NUOVA
    return Destinazione(modo, str(qs.value("destinazione/titolo", "")))


def salva(dest: Destinazione, qs: QSettings | None = None) -> None:
    qs = qs or _impostazioni()
    qs.setValue("destinazione/modo", dest.modo)
    qs.setValue("destinazione/titolo", dest.titolo)
    qs.sync()
