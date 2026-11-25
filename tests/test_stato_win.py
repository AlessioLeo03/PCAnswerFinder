from cerchia.stato_win import VK_LWIN, Stato, StatoWin

VK_E = 0x45


def test_pressione_breve_riapre_start():
    s = StatoWin()
    assert s.tasto(VK_LWIN, True, 0).blocca
    esito = s.tasto(VK_LWIN, False, 200)
    assert esito.blocca
    assert esito.reinvia == [(VK_LWIN, True), (VK_LWIN, False)]
    assert s.stato is Stato.RIPOSO


def test_pressione_lunga_avvia_e_blocca_rilascio():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    assert not s.tempo(499)
    assert s.tempo(500)
    esito = s.tasto(VK_LWIN, False, 900)
    assert esito.blocca and esito.reinvia == [] and not esito.avvia
    assert s.stato is Stato.RIPOSO


def test_ripetizione_automatica_oltre_soglia_avvia():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    esito = s.tasto(VK_LWIN, True, 530)
    assert esito.avvia and esito.blocca
    assert s.stato is Stato.AVVIATO


def test_combinazione_win_e_passa():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    esito = s.tasto(VK_E, True, 100)
    assert esito.blocca
    assert esito.reinvia == [(VK_LWIN, True), (VK_E, True)]
    assert not s.tasto(VK_E, False, 150).blocca
    assert not s.tasto(VK_LWIN, False, 200).blocca
    assert s.stato is Stato.RIPOSO
    assert not s.tempo(1000)


def test_altri_tasti_a_riposo_passano():
    assert not StatoWin().tasto(VK_E, True, 0).blocca


def test_durante_avviato_altri_tasti_passano_e_win_resta_bloccato():
    s = StatoWin()
    s.tasto(VK_LWIN, True, 0)
    s.tempo(600)
    assert not s.tasto(VK_E, True, 700).blocca
    assert s.tasto(VK_LWIN, True, 710).blocca


def test_rimanente_ms():
    st = StatoWin(soglia_ms=500)
    st.tasto(VK_LWIN, True, 1000)
    assert st.rimanente_ms(1400) == 100
    assert st.rimanente_ms(1495) == 10
    assert st.rimanente_ms(1600) == 10
