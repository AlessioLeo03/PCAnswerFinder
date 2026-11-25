# Prove a mano — PCAnswerFinder

Avvio: `.\.venv\Scripts\pythonw avvia.pyw` (oppure da "Avvia con Windows").

## Tasto Win
- [ ] Pressione breve di Win apre il menu Start.
- [ ] Win + E apre Esplora file; Win + Shift + S apre la cattura di Windows.
- [ ] Win tenuto premuto ~mezzo secondo apre lo strato; Start non si apre.

## Strato
- [ ] Schermo congelato, scurito, onda di luce.
- [ ] Cerchio → riquadro arrotondato, angoli trascinabili.
- [ ] Testo trascinato → parole azzurre; Copia testo attivo.
- [ ] Clic su un elemento → riquadro attorno all'elemento; clic sul desktop vuoto → "Nessun elemento qui, prova a cerchiare."
- [ ] Esc chiude senza inviare.
- [ ] Esc premuto subito, prima di qualsiasi clic, chiude lo strato.
- [ ] Con due monitor a ridimensionamento diverso il ritaglio corrisponde al disegno.

## Invio
- [ ] Invio → chat nuova in Claude con immagine e domanda, risposta avviata.
- [ ] Casella vuota → "Cosa c'è in questa immagine? Spiegamelo."
- [ ] Traduci → "Traduci in italiano il testo che vedi nell'immagine.", senza testo incollato.
- [ ] Domanda scritta → arriva solo la domanda con l'immagine, senza "Testo selezionato".
- [ ] Copia testo → "Testo copiato." e testo negli appunti.
- [ ] Menu "Chat aperta" → la selezione va nella chat aperta in Claude, nessuna chat nuova.
- [ ] Menu "Cerca chat…" con un titolo esistente → si apre quella chat e riceve la selezione.
- [ ] "Cerca chat…" con titolo vuoto → "Scrivi il titolo della chat", nessun invio.
- [ ] La scelta del menu e il titolo restano uguali alla volta successiva.
- [ ] Nel menu, scrivendo nel titolo compaiono le chat cercate in passato più attinenti; un clic la sceglie.
- [ ] Dopo l'onda di luce compare in alto "Cerchia, evidenzia o tocca qualcosa…"; sparisce al primo clic.
- [ ] Appunti ripristinati dopo l'invio.
- [ ] App di Claude chiusa → si apre e riceve la selezione.

## Avvio con Windows
- [ ] Spunta "Avvia con Windows", riavvia il PC: l'icona compare da sola.
- [ ] Togli la spunta: dopo il riavvio non parte.

## Errori
- [ ] Il file %LOCALAPPDATA%\PCAnswerFinder\errori.log raccoglie gli errori (se ce ne sono).

## Limiti noti
- Sopra programmi avviati come amministratore il tasto Win non viene intercettato.
- Win + L potrebbe non bloccare il PC mentre Win è in attesa del mezzo secondo.
- Gli appunti vengono ripristinati solo nei formati che Qt conosce (testo, HTML, immagini): formati privati di altri programmi possono andare persi.
- Le catture incollate restano nella cronologia degli appunti di Windows (Win + V).
