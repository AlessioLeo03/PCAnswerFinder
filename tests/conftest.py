import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from cerchia import chat_claude, destinazione, scorciatoia


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def impostazioni_di_prova(tmp_path, monkeypatch):
    """Le prove non toccano le scelte salvate dell'utente nel registro."""
    percorso = str(tmp_path / "impostazioni.ini")
    monkeypatch.setattr(destinazione, "_impostazioni", lambda: QSettings(percorso, QSettings.IniFormat))
    monkeypatch.setattr(chat_claude, "_titoli", [])
    monkeypatch.setattr(scorciatoia, "_impostazioni", lambda: QSettings(percorso, QSettings.IniFormat))
