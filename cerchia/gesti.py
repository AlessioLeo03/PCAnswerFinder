"""Logica pura dei gesti: classificazione, riquadri e selezione delle parole.

Tutte le coordinate sono pixel fisici, relativi all'angolo in alto a sinistra dello schermo.
"""
from dataclasses import dataclass
from enum import Enum, auto
from math import hypot

Punto = tuple[float, float]

SOGLIA_CLIC_PX = 6
MARGINE_TRATTO = 12
MARGINE_TESTO = 8
MINIMO_PX = 32


@dataclass(frozen=True)
class Rett:
    x: float
    y: float
    w: float
    h: float

    @property
    def destra(self) -> float:
        return self.x + self.w

    @property
    def basso(self) -> float:
        return self.y + self.h

    @property
    def centro(self) -> Punto:
        return (self.x + self.w / 2, self.y + self.h / 2)

    def contiene(self, p: Punto) -> bool:
        return self.x <= p[0] <= self.destra and self.y <= p[1] <= self.basso

    def unione(self, altro: "Rett") -> "Rett":
        x0, y0 = min(self.x, altro.x), min(self.y, altro.y)
        x1, y1 = max(self.destra, altro.destra), max(self.basso, altro.basso)
        return Rett(x0, y0, x1 - x0, y1 - y0)

    def allarga(self, m: float) -> "Rett":
        return Rett(self.x - m, self.y - m, self.w + 2 * m, self.h + 2 * m)

    def dentro(self, limite: "Rett") -> "Rett":
        x0, y0 = max(self.x, limite.x), max(self.y, limite.y)
        x1, y1 = min(self.destra, limite.destra), min(self.basso, limite.basso)
        return Rett(x0, y0, max(0, x1 - x0), max(0, y1 - y0))


@dataclass(frozen=True)
class Parola:
    testo: str
    rett: Rett
    riga: int


class TipoGesto(Enum):
    CLIC = auto()
    TESTO = auto()
    CERCHIO = auto()


def _distanza(a: Punto, b: Punto) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def indice_parola(p: Punto, parole: list[Parola]) -> int | None:
    for i, parola in enumerate(parole):
        if parola.rett.contiene(p):
            return i
    return None


def indice_parola_vicina(p: Punto, parole: list[Parola]) -> int | None:
    if not parole:
        return None
    i = indice_parola(p, parole)
    if i is not None:
        return i
    return min(range(len(parole)), key=lambda k: _distanza(p, parole[k].rett.centro))


def classifica(punti: list[Punto], parole: list[Parola]) -> TipoGesto:
    inizio = punti[0]
    if max(_distanza(inizio, q) for q in punti) < SOGLIA_CLIC_PX:
        return TipoGesto.CLIC
    i = indice_parola(inizio, parole)
    if i is not None:
        ys = [q[1] for q in punti]
        if max(ys) - min(ys) < 1.5 * parole[i].rett.h:
            return TipoGesto.TESTO
    return TipoGesto.CERCHIO


def _con_minimo(r: Rett, minimo: float) -> Rett:
    w, h = max(r.w, minimo), max(r.h, minimo)
    cx, cy = r.centro
    return Rett(cx - w / 2, cy - h / 2, w, h)


def riquadro_da_tratto(punti: list[Punto], limite: Rett) -> Rett:
    xs = [q[0] for q in punti]
    ys = [q[1] for q in punti]
    r = Rett(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).allarga(MARGINE_TRATTO)
    return _con_minimo(r, MINIMO_PX).dentro(limite)


def parole_tra(parole: list[Parola], i: int, j: int) -> list[Parola]:
    a, b = sorted((i, j))
    return parole[a:b + 1]


def parole_dentro(parole: list[Parola], r: Rett) -> list[Parola]:
    return [p for p in parole if r.contiene(p.rett.centro)]


def riquadro_parole(parole: list[Parola], limite: Rett) -> Rett:
    r = parole[0].rett
    for p in parole[1:]:
        r = r.unione(p.rett)
    return r.allarga(MARGINE_TESTO).dentro(limite)


def testo_di(parole: list[Parola]) -> str:
    righe: list[list[str]] = []
    ultima = None
    for p in parole:
        if p.riga != ultima:
            righe.append([])
            ultima = p.riga
        righe[-1].append(p.testo)
    return "\n".join(" ".join(r) for r in righe)


def sposta_angolo(r: Rett, angolo: int, p: Punto, limite: Rett) -> Rett:
    """Sposta un angolo del riquadro. angolo: 0 alto-sx, 1 alto-dx, 2 basso-sx, 3 basso-dx."""
    x0, y0, x1, y1 = r.x, r.y, r.destra, r.basso
    px = min(max(p[0], limite.x), limite.destra)
    py = min(max(p[1], limite.y), limite.basso)
    if angolo in (0, 2):
        x0 = min(px, x1 - MINIMO_PX)
    else:
        x1 = max(px, x0 + MINIMO_PX)
    if angolo in (0, 1):
        y0 = min(py, y1 - MINIMO_PX)
    else:
        y1 = max(py, y0 + MINIMO_PX)
    return Rett(x0, y0, x1 - x0, y1 - y0)
