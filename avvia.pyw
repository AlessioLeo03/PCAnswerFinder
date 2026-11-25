"""Avvia Cerchia e Chiedi senza finestra della console."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cerchia.avvio import main  # noqa: E402

main()
