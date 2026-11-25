"""Riconoscimento del testo con l'OCR incluso in Windows, eseguito in un thread."""
import asyncio
import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

from cerchia.cattura import png_da_immagine
from cerchia.gesti import Parola, Rett


async def _leggi(png: bytes) -> list[Parola] | None:
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

    motore = OcrEngine.try_create_from_user_profile_languages()
    if motore is None:
        return None
    flusso = InMemoryRandomAccessStream()
    scrittore = DataWriter(flusso)
    scrittore.write_bytes(png)
    await scrittore.store_async()
    scrittore.detach_stream()
    flusso.seek(0)
    decoder = await BitmapDecoder.create_async(flusso)
    bitmap = await decoder.get_software_bitmap_async()
    esito = await motore.recognize_async(bitmap)
    parole = []
    for n, riga in enumerate(esito.lines):
        for w in riga.words:
            b = w.bounding_rect
            parole.append(Parola(w.text, Rett(b.x, b.y, b.width, b.height), n))
    return parole


def leggi(png: bytes) -> list[Parola] | None:
    """Parole in ordine di lettura, oppure None se l'OCR di Windows non è disponibile."""
    try:
        return asyncio.run(_leggi(png))
    except Exception:
        return None


class LettoreOcr(QObject):
    # Emesso da un thread di lavoro: collegarlo a un metodo di un QObject (consegna in coda al thread grafico), mai a lambda/funzioni libere che toccano i widget.
    pronto = Signal(object)  # list[Parola] | None

    def avvia(self, img: QImage) -> None:
        threading.Thread(target=self._lavora, args=(img.copy(),), daemon=True).start()

    def _lavora(self, img: QImage) -> None:
        parole = leggi(png_da_immagine(img))
        try:
            self.pronto.emit(parole)
        except RuntimeError:  # lo strato è già stato chiuso
            pass
