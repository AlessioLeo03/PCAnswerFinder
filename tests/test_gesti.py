from cerchia.gesti import (
    Parola, Rett, TipoGesto, classifica, indice_parola_vicina, parole_dentro,
    parole_tra, riquadro_da_tratto, riquadro_parole, sposta_angolo,
)
from cerchia.gesti import testo_di as unisci_righe  # alias: evita che pytest raccolga testo_di come test

SCHERMO = Rett(0, 0, 1920, 1080)
PAROLE = [
    Parola("Ciao", Rett(100, 100, 80, 30), 0),
    Parola("mondo", Rett(190, 100, 100, 30), 0),
    Parola("seconda", Rett(100, 150, 120, 30), 1),
    Parola("riga", Rett(230, 150, 70, 30), 1),
]


def test_clic_se_movimento_piccolo():
    assert classifica([(500, 500), (503, 502), (501, 499)], PAROLE) is TipoGesto.CLIC


def test_testo_se_parte_su_parola_e_resta_sulla_riga():
    assert classifica([(110, 115), (200, 118), (280, 112)], PAROLE) is TipoGesto.TESTO


def test_cerchio_se_parte_fuori_dalle_parole():
    punti = [(400, 400), (600, 400), (600, 600), (400, 600)]
    assert classifica(punti, PAROLE) is TipoGesto.CERCHIO


def test_cerchio_se_parte_su_parola_ma_scende_in_verticale():
    assert classifica([(110, 115), (120, 300)], PAROLE) is TipoGesto.CERCHIO


def test_riquadro_da_tratto_con_margine():
    assert riquadro_da_tratto([(400, 400), (600, 450), (500, 600)], SCHERMO) == Rett(388, 388, 224, 224)


def test_riquadro_limitato_ai_bordi():
    r = riquadro_da_tratto([(2, 2), (300, 200)], SCHERMO)
    assert (r.x, r.y, r.destra, r.basso) == (0, 0, 312, 212)


def test_riquadro_dimensione_minima():
    r = riquadro_da_tratto([(500, 500), (502, 501)], SCHERMO)
    assert r.w == 32 and r.h == 32
    assert r.contiene((501, 500))


def test_parole_tra_su_due_righe_in_ordine_di_lettura():
    assert [p.testo for p in parole_tra(PAROLE, 3, 1)] == ["mondo", "seconda", "riga"]


def test_parola_vicina_quando_il_punto_e_fuori():
    assert indice_parola_vicina((320, 160), PAROLE) == 3


def test_parola_vicina_senza_parole():
    assert indice_parola_vicina((0, 0), []) is None


def test_parole_dentro_usa_il_centro():
    assert [p.testo for p in parole_dentro(PAROLE, Rett(90, 90, 160, 50))] == ["Ciao", "mondo"]


def test_testo_di_va_a_capo_tra_righe():
    assert unisci_righe(PAROLE) == "Ciao mondo\nseconda riga"


def test_riquadro_parole_unione_con_margine():
    assert riquadro_parole(PAROLE[:2], SCHERMO) == Rett(92, 92, 206, 46)


def test_sposta_angolo_basso_destra():
    assert sposta_angolo(Rett(100, 100, 200, 200), 3, (500, 450), SCHERMO) == Rett(100, 100, 400, 350)


def test_sposta_angolo_rispetta_minimo():
    assert sposta_angolo(Rett(100, 100, 200, 200), 0, (400, 400), SCHERMO) == Rett(268, 268, 32, 32)
