from cerchia.chat_claude import titoli_da_pulsanti


def test_titoli_solo_dai_pulsanti_altre_opzioni():
    nomi = ["Riduci a icona", "Altre opzioni per Domande Java SE 17", "Nuovo", "Altre opzioni per 3D",
            "Altre opzioni per Scorciatoia tastiera per contesto", "More options for Trip plan",
            "Altre opzioni per 3d", "Altre opzioni per   "]
    assert titoli_da_pulsanti(nomi) == ["Domande Java SE 17", "3D", "Scorciatoia tastiera per contesto", "Trip plan"]


def test_nessun_pulsante():
    assert titoli_da_pulsanti([]) == []
