/* Der Durchlauf im Browser — dieselbe Logik wie src/helfer/einstufung/fragefolge.py.
 *
 * Warum es diese zweite Fassung gibt: die Einstufung soll auf der Webseite
 * ohne Installation laufen und im installierten Programm genauso. Die Daten
 * sind dieselben (daten/aufbereitet/fragefolge.json, erzeugt aus den
 * YAML-Dateien), nur die Ablauflogik steht zweimal da.
 *
 * Das ist die gefährliche Stelle. Zwei Fassungen derselben Logik laufen
 * auseinander: beim Bau des Durchlaufs haben Fragefolge und Auswertung genau
 * das getan und dreissig von 217 amtlichen Beispielen gekostet. Darum gilt
 * hier: jede Änderung an einer der beiden Fassungen wird an der anderen
 * nachgemessen. scripts/pruefe_zwei_wege.py fährt beide mit denselben
 * Antworten und vergleicht Frage für Frage und Befund für Befund. Weicht
 * etwas ab, schlägt der Prüflauf fehl.
 */

export const ERFASST = "erfasst";
export const NICHT_ERFASST = "nicht_erfasst";
export const WEITER = "weiter";
export const ENDE = "ende";
export const BEDINGT = "bedingt";
export const TRIFFT_NICHT_ZU = "trifft_nicht_zu";

function folge(frage, antwort) {
  if (antwort === undefined || antwort === null || antwort === TRIFFT_NICHT_ZU) return WEITER;
  return antwort ? frage.bei_ja : frage.bei_nein;
}

function werten(fragen, antworten) {
  let schliesstAus = false;
  let traegt = false;
  let offen = false;
  for (const f of fragen) {
    const antwort = antworten[f.kennung];
    if (antwort === undefined) { offen = true; continue; }
    const fg = folge(f, antwort);
    if (fg === NICHT_ERFASST) schliesstAus = true;
    else if (fg === ERFASST) traegt = true;
  }
  if (schliesstAus) return NICHT_ERFASST;
  if (traegt) return ERFASST;
  return offen ? WEITER : NICHT_ERFASST;
}

export class Durchlauf {
  constructor(daten) {
    this.d = daten;
    this.aufbau = daten.aufbau || {};
    this.vorfragen = daten.vorfragen || [];
    this.hinweise = daten.hinweise || [];
    this.punkte = daten.punkte || [];
    this.filterfragen = daten.filterfragen || [];
    this.profilingfrage = daten.profilingfrage || null;
    this.ai = daten.anhang_i || {};
    this.bereichsfragen = daten.bereichsfragen || [];
  }

  vorfrageEintrag(kennung) {
    return (this.aufbau.vorfragen || []).find((e) => e.kennung === kennung) || {};
  }

  punktGesperrt(punkt, antworten) {
    for (const f of this.vorfragen) {
      const e = this.vorfrageEintrag(f.kennung);
      const betroffen = e.wirkt_auf || [];
      if (!betroffen.includes(punkt.fundstelle)) continue;
      if (antworten[f.kennung] === false && !e.nur_als_zusatz) return true;
    }
    return false;
  }

  bereichAbgewaehlt(punkt, antworten) {
    return antworten["bereich:" + punkt.bereich] === false;
  }

  bereichGesperrt(punkt, antworten) {
    const tor = (this.aufbau.tore_je_bereich || {})[punkt.bereich];
    if (!tor || tor === punkt.fundstelle) return false;
    const torpunkt = this.punkte.find((p) => p.fundstelle === tor);
    if (!torpunkt) return false;
    return antworten[torpunkt.hauptfrage.kennung] === false;
  }

  verbund(bereich) {
    return (this.aufbau.verbunde || []).find((v) => v.bereich === bereich) || null;
  }

  verbundpunktErfuellt(punkt, antworten) {
    const haupt = antworten[punkt.hauptfrage.kennung];
    if (haupt === undefined) return WEITER;
    if (haupt === false) return NICHT_ERFASST;
    const aufzaehlung = punkt.folgefragen.filter((f) => folge(f, true) === WEITER);
    const offen = punkt.folgefragen.some((f) => antworten[f.kennung] === undefined);
    for (const f of punkt.folgefragen) {
      if (folge(f, antworten[f.kennung]) === NICHT_ERFASST) return NICHT_ERFASST;
    }
    if (aufzaehlung.length && !aufzaehlung.some((f) => antworten[f.kennung] === true)) {
      return offen ? WEITER : NICHT_ERFASST;
    }
    return offen ? WEITER : ERFASST;
  }

  verbundbefund(bereich, antworten) {
    const v = this.verbund(bereich);
    if (!v) return NICHT_ERFASST;
    if (antworten["bereich:" + bereich] === false) return NICHT_ERFASST;
    const marke = v.sonderfall_hauptfrage_enthaelt || "";
    const regel = this.punkte.filter(
      (p) => p.bereich === bereich && !(marke && p.hauptfrage.text.includes(marke))
    );
    if (!regel.length) return NICHT_ERFASST;
    const offenErlaubt = v.darf_offen_bleiben || {};
    const markeOffen = offenErlaubt.hauptfrage_enthaelt || "";
    const befunde = [];
    let bedingt = false;
    for (const punkt of regel) {
      const befund = this.verbundpunktErfuellt(punkt, antworten);
      if (
        markeOffen &&
        punkt.hauptfrage.text.includes(markeOffen) &&
        befund === NICHT_ERFASST &&
        antworten[punkt.hauptfrage.kennung] !== false
      ) {
        bedingt = true;
        continue;
      }
      befunde.push(befund);
    }
    if (befunde.includes(NICHT_ERFASST)) return NICHT_ERFASST;
    if (befunde.includes(WEITER)) return WEITER;
    return bedingt ? BEDINGT : ERFASST;
  }

  punktbefund(punkt, antworten) {
    if (
      this.punktGesperrt(punkt, antworten) ||
      this.bereichGesperrt(punkt, antworten) ||
      this.bereichAbgewaehlt(punkt, antworten)
    ) {
      return NICHT_ERFASST;
    }
    if (this.verbund(punkt.bereich)) return NICHT_ERFASST;
    const haupt = antworten[punkt.hauptfrage.kennung];
    if (haupt === undefined) return WEITER;
    if (haupt === false) return NICHT_ERFASST;
    if (punkt.ist_bereichstor) return NICHT_ERFASST;
    return werten(punkt.folgefragen, antworten);
  }

  gruppeEntfaellt(gruppe, antworten) {
    for (const k of gruppe.entfaellt_wenn || []) {
      const f = (this.ai.fragen || {})[k];
      if (f && antworten[f.kennung] === true) return true;
    }
    return false;
  }

  anhangIBefund(antworten) {
    if (!this.ai.tor) return NICHT_ERFASST;
    const tor = antworten[this.ai.tor.kennung];
    if (tor === undefined) return WEITER;
    if (tor === false) return NICHT_ERFASST;
    const gattungen = this.ai.gattungen || [];
    if (!gattungen.some((g) => antworten[g.kennung])) {
      if (gattungen.some((g) => antworten[g.kennung] === undefined)) return WEITER;
      return NICHT_ERFASST;
    }
    for (const gruppe of this.ai.bedingungen || []) {
      if (this.gruppeEntfaellt(gruppe, antworten)) continue;
      const kennungen = (gruppe.eine_genuegt || [])
        .filter((k) => this.ai.fragen[k])
        .map((k) => this.ai.fragen[k].kennung);
      if (kennungen.some((k) => antworten[k] === undefined)) return WEITER;
      if (!kennungen.some((k) => antworten[k])) return NICHT_ERFASST;
      for (const k of gruppe.ausschluss || []) {
        const f = this.ai.fragen[k];
        if (!f) continue;
        if (antworten[f.kennung] === undefined) return WEITER;
        if (antworten[f.kennung]) return NICHT_ERFASST;
      }
    }
    return ERFASST;
  }

  naechsteAnhangI(antworten) {
    if (!this.ai.tor) return null;
    if (antworten[this.ai.tor.kennung] === undefined) return this.ai.tor;
    if (antworten[this.ai.tor.kennung] === false) return null;
    for (const g of this.ai.gattungen || []) {
      if (antworten[g.kennung] === undefined) return g;
    }
    if (!(this.ai.gattungen || []).some((g) => antworten[g.kennung])) return null;
    for (const gruppe of this.ai.bedingungen || []) {
      if (this.gruppeEntfaellt(gruppe, antworten)) continue;
      const kennungen = (gruppe.eine_genuegt || []).filter((k) => this.ai.fragen[k]);
      for (const k of kennungen) {
        if (antworten[this.ai.fragen[k].kennung] === undefined) return this.ai.fragen[k];
      }
      if (!kennungen.some((k) => antworten[this.ai.fragen[k].kennung])) return null;
      for (const k of gruppe.ausschluss || []) {
        const f = this.ai.fragen[k];
        if (f && antworten[f.kennung] === undefined) return f;
      }
    }
    return null;
  }

  naechste(antworten) {
    for (const f of this.vorfragen) {
      if (antworten[f.kennung] === undefined) return f;
      const e = this.vorfrageEintrag(f.kennung);
      if (antworten[f.kennung] === false && e.bei_nein === ENDE) return null;
    }
    const ai = this.naechsteAnhangI(antworten);
    if (ai) return ai;

    for (const f of this.bereichsfragen) {
      if (antworten[f.kennung] === undefined) return f;
    }

    const uebersprungen = new Set();
    for (const punkt of this.punkte) {
      if (uebersprungen.has(punkt.bereich)) continue;
      if (
        this.punktGesperrt(punkt, antworten) ||
        this.bereichGesperrt(punkt, antworten) ||
        this.bereichAbgewaehlt(punkt, antworten)
      ) continue;
      if (antworten[punkt.hauptfrage.kennung] === undefined) return punkt.hauptfrage;
      if (antworten[punkt.hauptfrage.kennung] === false) {
        if (punkt.ist_bereichstor) uebersprungen.add(punkt.bereich);
        continue;
      }
      for (const f of punkt.folgefragen) {
        if (antworten[f.kennung] === undefined) return f;
      }
    }

    const traegt =
      this.punkte.some((p) => this.punktbefund(p, antworten) === ERFASST) ||
      (this.aufbau.verbunde || []).some(
        (v) => this.verbundbefund(v.bereich, antworten) === ERFASST
      );
    if (traegt) {
      for (const f of this.filterfragen) {
        if (antworten[f.kennung] === undefined) return f;
      }
      if (this.filterfragen.some((f) => antworten[f.kennung]) && this.profilingfrage) {
        if (antworten[this.profilingfrage.kennung] === undefined) return this.profilingfrage;
      }
    }
    return null;
  }

  naechsteGruppe(antworten) {
    const erste = this.naechste(antworten);
    if (!erste) return [];
    const offen = (fs) => fs.filter((f) => antworten[f.kennung] === undefined);

    if (erste.stufe === "vorfrage") return offen(this.vorfragen);
    if (erste.stufe === "bereich") return offen(this.bereichsfragen);
    if (erste.stufe === "anhang_i") {
      if (this.ai.tor && erste.kennung === this.ai.tor.kennung) return [erste];
      if (erste.kennung.startsWith("anhang-i-gattung:")) return offen(this.ai.gattungen || []);
      return offen(Object.values(this.ai.fragen || {}));
    }
    if (erste.stufe === "filter") {
      if (this.profilingfrage && erste.kennung === this.profilingfrage.kennung) return [erste];
      return offen(this.filterfragen);
    }
    if (erste.kennung.startsWith("haupt:")) {
      const gruppe = [];
      const gesperrt = new Set();
      for (const punkt of this.punkte) {
        if (gesperrt.has(punkt.bereich)) continue;
        if (
          this.punktGesperrt(punkt, antworten) ||
          this.bereichGesperrt(punkt, antworten) ||
          this.bereichAbgewaehlt(punkt, antworten)
        ) continue;
        if (antworten[punkt.hauptfrage.kennung] !== undefined) {
          if (antworten[punkt.hauptfrage.kennung] === false && punkt.ist_bereichstor) {
            gesperrt.add(punkt.bereich);
          }
          continue;
        }
        gruppe.push(punkt.hauptfrage);
      }
      return gruppe;
    }
    let punkt = this.punkte.find((p) => p.folgefragen.some((f) => f.kennung === erste.kennung));
    if (!punkt) punkt = this.punkte.find((p) => p.fundstelle === erste.fundstelle);
    if (!punkt) return [erste];
    return offen(punkt.folgefragen);
  }

  ergebnis(antworten) {
    const ki = this.vorfragen.length ? this.vorfragen[0].kennung : "";
    if (antworten[ki] === false) {
      const e = this.vorfrageEintrag(ki);
      return {
        klasse: "kein_ki_system",
        getroffene_punkte: [],
        filter_greift: false,
        filter_grund: "",
        belege: [this.vorfragen[0].beleg],
        offene_punkte: [],
        endtext: e.endtext || "",
      };
    }
    if (this.anhangIBefund(antworten) === ERFASST) {
      const gattung = (this.ai.gattungen || []).find((g) => antworten[g.kennung]) || null;
      return {
        klasse: "hochrisiko_anhang_i",
        getroffene_punkte: [],
        filter_greift: false,
        filter_grund: "",
        belege: [this.ai.tor && this.ai.tor.beleg, gattung && gattung.beleg].filter(Boolean),
        offene_punkte: [],
        endtext:
          "Hohes Risiko über das Produktsicherheitsrecht: " +
          (gattung ? gattung.titel : "Produkt nach Anhang I") +
          ". Der Filter des Artikels 6 Absatz 3 gilt hier nicht — er betrifft nur Anhang III.",
        gattung: gattung,
      };
    }

    const getroffen = this.punkte.filter((p) => this.punktbefund(p, antworten) === ERFASST);
    const offen = this.punkte
      .filter((p) => this.punktbefund(p, antworten) === WEITER)
      .map((p) => p.fundstelle);
    for (const v of this.aufbau.verbunde || []) {
      const befund = this.verbundbefund(v.bereich, antworten);
      if (befund === ERFASST) {
        const erster = this.punkte.find((p) => p.bereich === v.bereich);
        if (erster) getroffen.push(erster);
      } else if (befund === BEDINGT) {
        const erster = this.punkte.find((p) => p.bereich === v.bereich);
        const offenErlaubt = v.darf_offen_bleiben || {};
        return {
          klasse: "hochrisiko_bedingt",
          getroffene_punkte: erster ? [erster] : [],
          filter_greift: false,
          filter_grund: "",
          belege: [offenErlaubt.beleg || ""],
          offene_punkte: offen,
          endtext: (offenErlaubt.wenn_offen || "").split(/\s+/).join(" ").trim(),
        };
      } else if (befund === WEITER) offen.push(v.bereich);
    }
    if (!getroffen.length) {
      return {
        klasse: "kein_hohes_risiko",
        getroffene_punkte: [],
        filter_greift: false,
        filter_grund: "",
        belege: [],
        offene_punkte: offen,
        endtext: "",
      };
    }
    const bedingung = this.filterfragen.find((f) => antworten[f.kennung] === true) || null;
    const profiling = this.profilingfrage ? antworten[this.profilingfrage.kennung] : undefined;
    if (bedingung && profiling === false) {
      return {
        klasse: "hochrisiko_ausnahme",
        getroffene_punkte: getroffen,
        filter_greift: true,
        filter_grund: bedingung.text,
        belege: [bedingung.beleg, this.profilingfrage && this.profilingfrage.beleg].filter(Boolean),
        offene_punkte: offen,
        endtext: "",
      };
    }
    return {
      klasse: "hochrisiko_anhang_iii",
      getroffene_punkte: getroffen,
      filter_greift: false,
      filter_grund: "",
      belege: getroffen.map((p) => p.hauptfrage.beleg).filter(Boolean),
      offene_punkte: offen,
      endtext: "",
    };
  }
}
