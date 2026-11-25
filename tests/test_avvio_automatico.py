import re
import sys
from pathlib import Path

from cerchia import avvio

PATTERN = re.compile(r'^"(?P<pythonw>[^"]+)" "(?P<script>[^"]+)"$')


def test_comando_avvio_forma_e_percorsi():
    comando = avvio._comando_avvio()
    assert isinstance(comando, str)
    m = PATTERN.match(comando)
    assert m is not None, comando
    pythonw = m.group("pythonw")
    script = Path(m.group("script"))
    assert script.name.lower() == "avvia.pyw"
    assert script.exists()
    if sys.executable.lower().endswith(r"\.venv\scripts\python.exe"):
        assert pythonw.lower().endswith(r"\.venv\scripts\pythonw.exe")


def test_avvio_automatico_attivo_restituisce_bool():
    # Solo lettura del registro: non scrive nulla.
    assert isinstance(avvio.avvio_automatico_attivo(), bool)
