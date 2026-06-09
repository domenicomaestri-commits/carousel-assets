---
name: carousel
description: >-
  Genera il carosello Instagram dell'account italiano di songwriting — i post
  "X ≠ Y" sul marchio ≠ (1080x1350 @2x). Usa questa skill quando l'utente dice
  "genera post di oggi", "nuovo carosello", "crea le slide", "fai il post di
  oggi", o chiede di produrre gli slide-01..07.png. Tema passato come argomento,
  es. /carousel "Bridge ≠ Middle 8".
argument-hint: "[X ≠ Y]"
---

# Carosello songwriting ("≠")

Genera un carosello a 7 slide nello stile del brand: sfondo bruno scuro, bianco
caldo + oro, marchio `≠` in alto a destra, contatore pagina in alto a sinistra,
numero filigrana sui content, pill oro sulla CTA. Una sola distinzione per post
(`X ≠ Y`), in italiano, voce educational e concisa.

Il rendering è uno script Pillow guidato da JSON. Font (Inter, OFL) e Pillow
sono gestiti automaticamente, quindi lo stesso comando funziona identico su
desktop (Mac) e su Claude Code web/mobile (iPhone): la skill vive nel repo e
viaggia col clone.

## Procedura

1. **Tema.** Usa `$ARGUMENTS` se fornito (es. `Bridge ≠ Middle 8`); altrimenti
   chiedi all'utente la distinzione del giorno. Un post = una distinzione.

2. **Scrivi lo spec** in `${CLAUDE_SKILL_DIR}/specs/<slug>.json` seguendo lo
   schema (`${CLAUDE_SKILL_DIR}/schema.json`) e l'esempio di riferimento
   (`${CLAUDE_SKILL_DIR}/specs/pre-chorus-vs-chorus.json`). Arco a 7 slide:
   1. `cover` — titolo a due tinte: `title_white` (la tesi) + `title_gold` (la posta in gioco)
   2. `content` — definizione di cosa è
   3. `content` — a cosa serve / la funzione
   4. `content` — gli strumenti / lista con bullet `—` oro (`{"t":"—  ","w":"med","c":"GOLD"}`)
   5. `content` — l'errore comune
   6. `content` — la regola / takeaway
   7. `cta` — "Vuoi capire come strutturare le tue canzoni?" + pill `pill_text`

   Regole di voce: italiano conciso e minuscolo nel body; enfasi con run
   `{"w":"bold","c":"WHITE"}`; riga vuota = run `{"t":" ","size":10}`; label in
   maiuscolo. **Niente emoji a colori** (Pillow non le renderizza): usa testo o
   frecce Unicode (`↓ → •`). Non mettere `out_dir` assoluto nello spec.

3. **Archivia** il post attuale prima di sovrascrivere. Leggi lo slug attivo da
   `${CLAUDE_SKILL_DIR}/specs/_current.txt`, poi:
   `git mv slide-01.png slides/<slug-precedente>-slide-01.png` (… fino a 07).
   Aggiorna `_current.txt` col nuovo slug.

4. **Render** dalla root del repo:
   `python3 ${CLAUDE_SKILL_DIR}/render.py ${CLAUDE_SKILL_DIR}/specs/<slug>.json --out .`
   Produce `slide-01.png … slide-07.png` (2160×2700) nella root.

5. **Verifica e mostra.** Conferma 7 PNG @ 2160×2700, mostrali con SendUserFile,
   riassumi la distinzione e le label. Non fare commit/push automatico se non
   richiesto.

## Verifica anti-regressione (golden-master)

`.claude/verify.sh` rende lo spec di riferimento e lo confronta (tollerante
all'anti-aliasing) con `${CLAUDE_SKILL_DIR}/tests/reference/`. Verde = il
generatore non è regredito. Lo Stop hook in `.claude/settings.json` blocca il
completamento finché è rosso. Se modifichi `render.py` e cambi
intenzionalmente l'output, **rigenera la reference**:
`python3 render.py specs/pre-chorus-vs-chorus.json --out tests/reference`.

## Note tecniche

- Costanti di layout (size, interlinee, cy, gap, colori label, geometria pill)
  sono fissate nelle funzioni `render_*`: **non** vanno nello spec. Lo spec
  contiene solo testi, label e (opz.) `title_size`.
- Font bundlato in `assets/Inter.ttf` (SIL OFL 1.1, vedi `assets/OFL.txt`).
- Su web l'ambiente deve avere accesso rete **Trusted** (o PyPI) per installare
  Pillow al primo run; un hook SessionStart opzionale può pre-installarlo.
