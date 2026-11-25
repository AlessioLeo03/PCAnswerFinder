"""Titoli delle chat/sessioni visibili nella barra laterale dell'app desktop di Claude (UI Automation).

La barra laterale mette accanto a ogni chat un pulsante "Altre opzioni per <titolo>": da quei pulsanti
si ricavano i titoli, senza confonderli con altri link della pagina. La lettura gira in un thread a parte
e il risultato resta in memoria per il menu "Cerca chat".
"""
import logging
import threading
import time

PREFISSI = ("Altre opzioni per ", "More options for ")
LIMITE_S = 4.0
PROFONDITA = 40

_titoli: list[str] = []
_in_corso = threading.Lock()


def titoli_da_pulsanti(nomi: list[str]) -> list[str]:
    """Dai nomi dei pulsanti ai titoli delle chat, nell'ordine della barra laterale, senza doppioni."""
    visti: set[str] = set()
    titoli = []
    for nome in nomi:
        for prefisso in PREFISSI:
            if nome.startswith(prefisso):
                titolo = nome[len(prefisso):].strip()
                if titolo and titolo.casefold() not in visti:
                    visti.add(titolo.casefold())
                    titoli.append(titolo)
                break
    return titoli


def leggi_titoli(hwnd: int) -> list[str]:
    import uiautomation as auto

    nomi = []
    inizio = time.monotonic()
    with auto.UIAutomationInitializerInThread():
        radice = auto.ControlFromHandle(hwnd)
        for ctrl, _prof in auto.WalkControl(radice, maxDepth=PROFONDITA):
            if time.monotonic() - inizio > LIMITE_S:
                break
            if ctrl.ControlTypeName == "ButtonControl":
                nomi.append(ctrl.Name or "")
    return titoli_da_pulsanti(nomi)


def titoli() -> list[str]:
    """Ultimi titoli letti (vuoto finché la prima lettura non è finita)."""
    return list(_titoli)


def aggiorna_in_background() -> None:
    """Rilegge i titoli senza bloccare l'interfaccia; ignora la richiesta se una lettura è già in corso."""
    if not _in_corso.acquire(blocking=False):
        return

    def lavoro() -> None:
        global _titoli
        try:
            from cerchia.invio_claude import trova_finestra
            hwnd = trova_finestra()
            if hwnd:
                letti = leggi_titoli(hwnd)
                if letti:
                    _titoli = letti
        except Exception:
            logging.exception("lettura dei titoli delle chat")
        finally:
            _in_corso.release()

    threading.Thread(target=lavoro, daemon=True).start()
