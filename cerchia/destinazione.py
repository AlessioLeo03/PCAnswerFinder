"""Dove mandare la selezione nell'app di Claude: chat nuova, chat aperta o chat cercata per titolo."""
from dataclasses import dataclass

from PySide6.QtCore import QSettings

NUOVA = "nuova"
APERTA = "aperta"
CERCA = "cerca"
MAX_RECENTI = 20

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
    if dest.modo == CERCA and dest.titolo.strip():
        qs.setValue("destinazione/recenti", aggiungi_recente(recenti(qs), dest.titolo))
    qs.sync()


def recenti(qs: QSettings | None = None) -> list[str]:
    """Titoli di chat cercati in passato, dal più recente."""
    qs = qs or _impostazioni()
    valore = qs.value("destinazione/recenti", [])
    if isinstance(valore, str):  # QSettings restituisce una stringa se la lista ha un solo elemento
        valore = [valore]
    return [str(v) for v in (valore or []) if str(v).strip()]


def aggiungi_recente(elenco: list[str], titolo: str) -> list[str]:
    """Mette il titolo in cima, senza doppioni (maiuscole ignorate), al massimo MAX_RECENTI."""
    titolo = titolo.strip()
    resto = [t for t in elenco if t.casefold() != titolo.casefold()]
    return ([titolo] + resto)[:MAX_RECENTI]


def unisci(*elenchi: list[str]) -> list[str]:
    """Unisce più elenchi di titoli tenendo il primo di ogni doppione (maiuscole ignorate)."""
    visti: set[str] = set()
    tutti = []
    for elenco in elenchi:
        for t in elenco:
            if t.casefold() not in visti:
                visti.add(t.casefold())
                tutti.append(t)
    return tutti


def suggerimenti(elenco: list[str], testo: str, quanti: int = 6) -> list[str]:
    """Titoli più attinenti a quanto scritto: prima quelli che iniziano così, poi quelli che lo contengono.

    Dentro ogni gruppo resta l'ordine dal più recente. Testo vuoto: i più recenti.
    """
    t = testo.strip().casefold()
    if not t:
        return elenco[:quanti]
    inizio = [x for x in elenco if x.casefold().startswith(t)]
    parola = [x for x in elenco if x not in inizio and any(p.startswith(t) for p in x.casefold().split())]
    dentro = [x for x in elenco if x not in inizio and x not in parola and t in x.casefold()]
    return (inizio + parola + dentro)[:quanti]
