import {Durchlauf, TRIFFT_NICHT_ZU} from "./durchlauf.js";

const buehne = document.getElementById("buehne");
const taktText = document.getElementById("takt-text");
const taktRechts = document.getElementById("takt-rechts");
const takt = document.getElementById("takt");
const ablauf = document.getElementById("ablauf");

let d = null, antworten = {}, schritt = 0, verlauf = [];

const KLASSEN = {
  hochrisiko_anhang_iii: {wort:"Hohes Risiko", stil:"hoch", lage:"Einstufung",
    satz:"Ihr System fällt nach Artikel 6 Absatz 2 und Anhang III unter die Hochrisiko-Systeme."},
  hochrisiko_anhang_i: {wort:"Hohes Risiko", stil:"hoch", lage:"Einstufung",
    satz:"Ihr System fällt nach Artikel 6 Absatz 1 über das Produktsicherheitsrecht unter die Hochrisiko-Systeme."},
  hochrisiko_bedingt: {wort:"Bedingt hohes Risiko", stil:"hoch", lage:"Einstufung",
    satz:"Ihr System erfüllt alle Voraussetzungen bis auf eine, die Sie nicht wissen können."},
  hochrisiko_ausnahme: {wort:"Ausnahme greift", stil:"", lage:"Einstufung",
    satz:"Ihr System fällt unter Anhang III, nimmt aber nach Artikel 6 Absatz 3 eine Ausnahme in Anspruch. Diese Ausnahme ist zu dokumentieren und das System ist zu registrieren."},
  kein_hohes_risiko: {wort:"Kein hohes Risiko", stil:"minimal", lage:"Einstufung",
    satz:"Nach Ihren Angaben fällt Ihr System in keinen der Anwendungsfälle des Anhangs I oder III."},
  kein_ki_system: {wort:"Kein KI-System", stil:"minimal", lage:"Einstufung",
    satz:"Was Sie beschrieben haben, ist nach Artikel 3 Nummer 1 kein KI-System."},
};

function el(tag, attrs = {}, kinder = []) {
  const k = document.createElement(tag);
  for (const [n, v] of Object.entries(attrs)) {
    if (n === "text") k.textContent = v;
    else if (n === "html") k.innerHTML = v;
    else k.setAttribute(n, v);
  }
  for (const kind of [].concat(kinder)) if (kind) k.append(kind);
  return k;
}

/* Der Ablauf links zeigt den Gang der Pruefung, nicht die Zahl der Schritte:
 * wie viele Nachfragen kommen, haengt von den Antworten ab. Fuenf Abschnitte
 * sind es immer. */
function phaseVon(frage) {
  if (!frage) return 1;
  if (frage.stufe === "vorfrage") return 1;
  if (frage.stufe === "bereich") return 2;
  if (frage.stufe === "filter") return 4;
  return 3;
}

function ablaufSetzen(phase) {
  for (const li of ablauf.children) {
    const n = Number(li.dataset.phase);
    li.classList.toggle("jetzt", n === phase);
    li.classList.toggle("fertig", n < phase);
    li.firstElementChild.textContent = n < phase ? "✓" : String(n);
  }
}

function taktSetzen(text, rechts, anteil) {
  taktText.textContent = text;
  taktRechts.textContent = rechts || "";
  takt.style.setProperty("--anteil", (anteil || 0) + "%");
}

function start() {
  buehne.replaceChildren(
    el("h2", {text:"Die Einstufung beginnt mit drei Fragen zum System"}),
    el("p", {text:"Danach fragt der Helfer nur noch das, was Ihre Antworten offenlassen. Am Ende "
      + "steht die Klasse, die Begründung und die Stelle im Gesetz."}),
    el("p", {text:"Geraten wird dabei nicht: die Einstufung entsteht aus Ihren Antworten und dem "
      + "Regelwerk, nicht aus einem Sprachmodell. Darum trägt jede Frage die Absatznummer der "
      + "amtlichen Auslegung, auf der sie beruht."}),
    el("p", {class:"leise", text:"Nichts von Ihren Angaben verlässt Ihr Gerät. Kein Server, "
      + "keine Anmeldung, keine Speicherung."}),
    el("div", {class:"aktionen"}, [
      el("button", {class:"knopf", id:"los", text:"Einstufung beginnen"}),
    ]),
    el("p", {class:"quelle", text:"Die Fragen stammen Zeile für Zeile aus dem Verordnungstext "
      + "und dem Entwurf der Leitlinien der Europäischen Kommission vom 19. Mai 2026. Jede nennt "
      + "den Absatz, auf dem sie beruht."}),
  );
  document.getElementById("los").onclick = () => { schritt = 0; verlauf = []; antworten = {}; zeichnen(); };
  ablaufSetzen(0);
  taktSetzen("Bereit", "", 0);
  document.getElementById("stand").textContent = "Stand der Daten: " + (d.d.stand || "—");
}

function bereichsname(frage) {
  const b = (d.aufbau.bereiche || []).find((x) => frage.fundstelle.startsWith(x.fundstelle));
  return b ? b.titel : frage.titel || "";
}

function ueberschriftFuer(erste) {
  if (erste.stufe === "vorfrage") return "Zuerst drei Fragen zum System selbst";
  if (erste.stufe === "bereich") return "Womit hat Ihr System zu tun?";
  if (erste.kennung.startsWith("haupt:")) return bereichsname(erste) || "Genauer nachgefragt";
  if (erste.kennung.startsWith("anhang-i-gattung:")) return "Um welches Produkt geht es?";
  if (erste.stufe === "anhang_i") return "Zum Produkt und zur Prüfung";
  if (erste.stufe === "filter") return "Ausnahme nach Artikel 6 Absatz 3";
  return bereichsname(erste) || "Zu Ihrem System";
}

function zeichnen() {
  const gruppe = d.naechsteGruppe(antworten);
  if (!gruppe.length) return befundZeigen();
  schritt += 1;

  const erste = gruppe[0];
  const phase = phaseVon(erste);
  ablaufSetzen(phase);
  taktSetzen(`Schritt ${schritt} — ` + ueberschriftFuer(erste),
    gruppe.length === 1 ? "1 Frage" : `${gruppe.length} Fragen`,
    Math.min(92, Math.round((schritt / Math.max(schritt + 1, 6)) * 100)));

  const teile = [el("h2", {text:ueberschriftFuer(erste)})];
  if (erste.stufe === "bereich") {
    teile.push(el("p", {class:"hinweis", text:"Mehrfachnennung möglich. Was nicht zutrifft, "
      + "bitte mit Nein beantworten — dann fragt der Helfer nicht weiter danach. Diese acht "
      + "Sätze sortieren nur; entschieden wird danach."}));
  }

  const liste = el("ul", {class:"fragen"});
  let letzterBereich = null;
  for (const f of gruppe) {
    if (f.kennung.startsWith("haupt:")) {
      const b = bereichsname(f);
      if (b && b !== letzterBereich) {
        liste.append(el("li", {class:"abschnitt", text:b}));
        letzterBereich = b;
      }
    }
    const zeile = el("li", {class:"frage"});
    const marge = el("div", {class:"marge"});
    if (f.beleg) {
      marge.append(el("b", {text:"Absatz " + String(f.beleg).replace(/[()]/g, "")}));
      marge.append(el("span", {text:"Leitlinien der Kommission"}));
    }
    const inhalt = el("div");
    inhalt.append(el("p", {class:"fragetext", text:f.text}));
    const wahl = el("div", {class:"wahl", role:"group"});
    for (const [wert, wort] of [[true,"Ja"],[false,"Nein"],[TRIFFT_NICHT_ZU,"Weiß ich nicht"]]) {
      const b = el("button", {type:"button", "aria-pressed":"false", text:wort});
      b.onclick = () => {
        antworten[f.kennung] = wert;
        for (const g of wahl.children) g.setAttribute("aria-pressed","false");
        b.setAttribute("aria-pressed","true");
        pruefeWeiter();
      };
      wahl.append(b);
    }
    inhalt.append(wahl);
    if (f.wirkung) inhalt.append(el("p", {class:"wirkung", text:f.wirkung}));
    zeile.append(marge, inhalt);
    liste.append(zeile);
  }
  teile.push(liste);

  const weiter = el("button", {class:"knopf", id:"weiter", text:"Weiter", disabled:""});
  weiter.onclick = () => { verlauf.push({...antworten}); zeichnen(); };
  const zurueck = el("button", {class:"knopf leer", text:"Zurück"});
  zurueck.onclick = () => {
    if (!verlauf.length) { schritt = 0; return start(); }
    antworten = verlauf.pop(); schritt = Math.max(0, schritt - 2); zeichnen();
  };
  const offen = el("span", {class:"offen", id:"offen"});
  teile.push(el("div", {class:"aktionen"}, [weiter, zurueck, offen]));

  buehne.replaceChildren(...teile);
  window.scrollTo({top:0, behavior:"instant"});
  pruefeWeiter();

  function pruefeWeiter() {
    const fehlen = gruppe.filter((f) => antworten[f.kennung] === undefined).length;
    const w = document.getElementById("weiter");
    const o = document.getElementById("offen");
    if (fehlen) {
      w.setAttribute("disabled","");
      o.textContent = fehlen === 1 ? "Noch eine Frage offen" : `Noch ${fehlen} Fragen offen`;
    } else {
      w.removeAttribute("disabled");
      o.textContent = "";
    }
  }
}

function fundstelleLesbar(s) {
  return s.replace("KI-VO/anh-III/nr-", "Anhang III Nummer ")
          .replace("KI-VO/anh-I", "Anhang I")
          .replace(/-([a-e])$/, " Buchstabe $1");
}

function befundZeigen() {
  const e = d.ergebnis(antworten);
  const k = KLASSEN[e.klasse] || KLASSEN.kein_hohes_risiko;
  ablaufSetzen(5);
  taktSetzen("Befund", `${schritt} Schritte`, 100);

  const teile = [el("div", {class:"befund " + k.stil}, [
    el("p", {class:"lage", text:k.lage}),
    el("p", {class:"urteil", text:k.wort}),
    el("p", {text:e.endtext || k.satz}),
  ])];

  if (e.getroffene_punkte.length) {
    const dl = el("dl");
    for (const p of e.getroffene_punkte) {
      dl.append(el("dt", {text:p.titel || p.bereich}));
      dl.append(el("dd", {class:"stelle", text:fundstelleLesbar(p.fundstelle)}));
      dl.append(el("dd", {class:"leise", text:p.hauptfrage.text}));
    }
    teile.push(el("section", {class:"block"}, [el("h3", {text:"Die Stelle, auf der das beruht"}), dl]));
  }
  if (e.filter_greift) {
    teile.push(el("section", {class:"block"}, [
      el("h3", {text:"Welche Ausnahme greift"}), el("p", {text:e.filter_grund})]));
  }
  if (!e.getroffene_punkte.length && !e.filter_greift) {
    teile.push(el("section", {class:"block"}, [
      el("h3", {text:"Was jetzt gilt"}),
      el("p", {text:"Es bleibt die Pflicht zur KI-Kompetenz nach Artikel 4: wer KI einsetzt oder "
        + "anbietet, muss dafür sorgen, dass die damit befassten Personen sie verstehen. "
        + "Werden personenbezogene Daten verarbeitet, gilt daneben die Datenschutz-Grundverordnung."}),
      el("p", {class:"leise", text:"Ändert sich der Zweck des Systems, ändert sich die Einstufung. "
        + "Dann lohnt ein neuer Durchlauf."}),
    ]));
  }
  if (e.belege.length) {
    teile.push(el("p", {class:"beleg", text:"Leitlinien der Kommission, Absätze " + e.belege.map((b) => String(b).replace(/[()]/g, "")).join(", ")}));
  }

  for (const p of e.getroffene_punkte) {
    if (!p.beispiele.length) continue;
    const auf = el("details");
    auf.append(el("summary", {text:`${p.beispiele.length} amtliche Beispiele zu dieser Stelle`}));
    for (const b of p.beispiele) {
      const ja = b.wertung === "hochrisiko";
      auf.append(el("div", {class:"beispiel"}, [
        el("p", {class:"wertung " + (ja ? "ja" : "nein"), text:ja ? "Erfasst" : "Nicht erfasst"}),
        el("p", {text:b.lage}),
        b.begruendung ? el("p", {class:"leise", text:b.begruendung}) : null,
        b.beleg ? el("p", {class:"beleg", text:"Absatz " + String(b.beleg).replace(/[()]/g, "")}) : null,
      ]));
    }
    teile.push(auf);
  }

  const nochmal = el("button", {class:"knopf leer", text:"Von vorn"});
  nochmal.onclick = () => { antworten = {}; schritt = 0; verlauf = []; start(); };
  teile.push(el("div", {class:"aktionen"}, [nochmal]));

  buehne.replaceChildren(...teile);
  window.scrollTo({top:0, behavior:"instant"});
}

fetch("./fragefolge.json")
  .then((r) => r.json())
  .then((daten) => { d = new Durchlauf(daten); start(); })
  .catch(() => {
    buehne.replaceChildren(
      el("h2", {text:"Die Fragen lassen sich nicht laden"}),
      el("p", {text:"Die Seite braucht die Datei fragefolge.json im selben Ordner. "
        + "Laden Sie die Seite neu; bleibt es dabei, fehlt die Datei auf dem Server."}));
  });
