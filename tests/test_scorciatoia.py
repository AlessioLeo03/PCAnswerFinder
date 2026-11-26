from PySide6.QtCore import QSettings

from cerchia import scorciatoia
from cerchia.scorciatoia import PREDEFINITA, Registratore, Scorciatoia
from cerchia.stato_win import VK_MASCHERA, Stato, StatoCombinazione, StatoWin

LCTRL, RCTRL, LSHIFT, LALT, LWIN, RWIN = 0xA2, 0xA3, 0xA0, 0xA4, 0x5B, 0x5C
Q, Z, F9, C = ord("Q"), ord("Z"), 0x78, ord("C")


def _registra(*eventi):
    r = Registratore()
    esito = False
    for vk, giu in eventi:
        esito = r.tasto(vk, giu)
    return esito


# ---------- nomi ----------

def test_nomi():
    assert Scorciatoia(Q, frozenset({"maiusc", "ctrl"})).nome() == "Ctrl + Maiusc + Q"
    assert Scorciatoia(Z, frozenset({"win"})).nome() == "Win + Z"
    assert Scorciatoia(0x20, frozenset({"alt", "ctrl", "win", "maiusc"})).nome() == "Win + Ctrl + Alt + Maiusc + Spazio"
    assert PREDEFINITA.nome() == "Tieni premuto Win"
    assert Scorciatoia(RCTRL, lunga=True).nome() == "Tieni premuto Ctrl destro"
    assert Scorciatoia(F9, lunga=True).nome() == "Tieni premuto F9"


# ---------- registrazione ----------

def test_registra_combinazione():
    s = _registra((LCTRL, True), (LSHIFT, True), (Q, True), (Q, False), (LSHIFT, False), (LCTRL, False))
    assert s == Scorciatoia(Q, frozenset({"ctrl", "maiusc"}))


def test_registra_conta_solo_il_primo_tasto_normale():
    s = _registra((LWIN, True), (Z, True), (Q, True), (Z, False), (Q, False), (LWIN, False))
    assert s == Scorciatoia(Z, frozenset({"win"}))


def test_registra_tasto_singolo_diventa_tieni_premuto():
    assert _registra((F9, True), (F9, True), (F9, False)) == Scorciatoia(F9, lunga=True)
    assert _registra((RCTRL, True), (RCTRL, False)) == Scorciatoia(RCTRL, lunga=True)


def test_registra_solo_modificatori_non_vale():
    assert _registra((LCTRL, True), (LSHIFT, True), (LSHIFT, False), (LCTRL, False)) is None


def test_registrazione_non_finita_finche_ci_sono_tasti_giu():
    r = Registratore()
    assert r.tasto(LCTRL, True) is False
    assert r.tasto(Q, True) is False
    assert r.tasto(Q, False) is False
    assert r.tasto(LCTRL, False) == Scorciatoia(Q, frozenset({"ctrl"}))


def test_rilascio_di_un_tasto_premuto_prima_viene_ignorato():
    r = Registratore()
    assert r.tasto(0x0D, False) is False  # Invio usato per premere il pulsante
    assert r.tasto(F9, True) is False
    assert r.tasto(F9, False) == Scorciatoia(F9, lunga=True)


# ---------- avvisi ----------

def test_avvisi():
    assert Scorciatoia(C, frozenset({"ctrl"})).avviso()
    assert Scorciatoia(ord("A"), lunga=True).avviso()
    assert Scorciatoia(Q, frozenset({"maiusc"})).avviso()
    assert Scorciatoia(0x73, frozenset({"alt"})).avviso()  # Alt+F4
    assert Scorciatoia(Q, frozenset({"ctrl", "maiusc"})).avviso() is None
    assert PREDEFINITA.avviso() is None
    assert Scorciatoia(F9, lunga=True).avviso() is None


# ---------- salvataggio ----------

def _qs(tmp_path):
    return QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)


def test_predefinita_se_niente_salvato(tmp_path):
    assert scorciatoia.carica(_qs(tmp_path)) == PREDEFINITA


def test_salva_e_ricarica(tmp_path):
    for s in (Scorciatoia(Q, frozenset({"ctrl", "maiusc"})), Scorciatoia(F9, lunga=True, soglia_ms=800),
              Scorciatoia(Z, frozenset({"win"}))):
        scorciatoia.salva(s, _qs(tmp_path))
        assert scorciatoia.carica(_qs(tmp_path)) == s


def test_valori_rovinati_tornano_alla_predefinita(tmp_path):
    qs = _qs(tmp_path)
    qs.setValue("scorciatoia/tasto", "boh")
    assert scorciatoia.carica(qs) == PREDEFINITA
    qs.setValue("scorciatoia/tasto", Q)
    qs.setValue("scorciatoia/lunga", "false")
    qs.setValue("scorciatoia/modificatori", "")
    assert scorciatoia.carica(qs) == PREDEFINITA  # una combinazione senza modificatori non è ammessa


# ---------- macchina a stati della combinazione ----------

def test_combinazione_scatta_e_blocca_il_tasto():
    st = StatoCombinazione(frozenset({"ctrl", "maiusc"}), Q)
    assert not st.tasto(LCTRL, True, 0).blocca
    assert not st.tasto(LSHIFT, True, 10).blocca
    e = st.tasto(Q, True, 20)
    assert e.blocca and e.avvia and e.reinvia == []
    r = st.tasto(Q, True, 60)  # ripetizione
    assert r.blocca and not r.avvia
    assert st.tasto(Q, False, 80).blocca
    assert st.stato is Stato.RIPOSO
    assert not st.tasto(LSHIFT, False, 90).blocca


def test_combinazione_non_esatta_non_scatta():
    st = StatoCombinazione(frozenset({"ctrl"}), Q)
    st.tasto(LCTRL, True, 0)
    st.tasto(LSHIFT, True, 0)
    e = st.tasto(Q, True, 10)
    assert not e.blocca and not e.avvia
    assert not StatoCombinazione(frozenset({"ctrl"}), Q).tasto(Q, True, 0).avvia  # Q da sola


def test_combinazione_con_win_maschera_start():
    st = StatoCombinazione(frozenset({"win"}), Z)
    st.tasto(RWIN, True, 0)
    e = st.tasto(Z, True, 10)
    assert e.avvia and e.reinvia == [(VK_MASCHERA, True), (VK_MASCHERA, False)]
    assert not st.tasto(RWIN, False, 30).blocca  # Win si rilascia normalmente: il tasto maschera evita Start


def test_altri_tasti_passano():
    st = StatoCombinazione(frozenset({"ctrl"}), Q)
    st.tasto(LCTRL, True, 0)
    assert not st.tasto(C, True, 10).blocca


# ---------- tasto lungo diverso da Win ----------

def test_tieni_premuto_f9():
    st = StatoWin(800, Scorciatoia(F9, lunga=True).tasti_lunghi())
    assert st.tasto(F9, True, 0).blocca
    assert not st.tempo(700)
    assert st.tempo(800)
    assert st.tasto(F9, False, 900).blocca
    corto = StatoWin(800, (F9,))
    corto.tasto(F9, True, 0)
    assert corto.tasto(F9, False, 100).reinvia == [(F9, True), (F9, False)]
    assert not StatoWin(800, (F9,)).tasto(LWIN, True, 0).blocca
