import {Durchlauf, TRIFFT_NICHT_ZU} from "./durchlauf.js";

const buehne = document.getElementById("buehne");
let d = null, antworten = {}, schritt = 0, verlauf = [];

const KLASSEN = {
  hochrisiko_anhang_iii: {wort:"Hohes Risiko", zeichen:"▲", stil:"hoch",
    satz:"Ihr System fällt nach Artikel 6 Absatz 2 und Anhang III unter die Hochrisiko-Systeme."},
  hochrisiko_anhang_i: {wort:"Hohes Risiko", zeichen:"▲", stil:"hoch",
    satz:"Ihr System fällt nach Artikel 6 Absatz 1 über das Produktsicherheitsrecht unter die Hochrisiko-Systeme."},
  hochrisiko_bedingt: {wort:"Bedingt hohes Risiko", zeichen:"▲", stil:"hoch",
    satz:"Ihr System erfüllt alle Voraussetzungen bis auf eine, die Sie nicht wissen können."},
  hochrisiko_ausnahme: {wort:"Ausnahme greift", zeichen:"◆", stil:"",
    satz:"Ihr System fällt unter Anhang III, nimmt aber nach Artikel 6 Absatz 3 eine Ausnahme in Anspruch. Diese Ausnahme ist zu dokumentieren und das System ist zu registrieren."},
  kein_hohes_risiko: {wort:"Kein hohes Risiko", zeichen:"●", stil:"minimal",
    satz:"Nach Ihren Angaben fällt Ihr System in keinen der Anwendungsfälle des Anhangs I oder III."},
  kein_ki_system: {wort:"Kein KI-System", zeichen:"○", stil:"minimal",
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

function start() {
  buehne.replaceChildren(
    el("div", {class:"karte"}, [
      el("h2", {text:"Was dieses Werkzeug leistet"}),
      el("p", {text:"Es stellt Ihnen die Fragen, die ein Jurist stellen würde, und sagt Ihnen danach, "
        + "in welche Klasse der KI-Verordnung Ihr System fällt — und an welcher Stelle des Gesetzes das steht."}),
      el("p", {text:"Es rät nicht. Die Einstufung entsteht aus Ihren Antworten und dem Regelwerk, "
        + "nicht aus einem Sprachmodell. Darum steht an jeder Frage die Absatznummer der amtlichen "
        + "Auslegung, auf der sie beruht."}),
      el("p", {class:"leise", text:"Nichts von Ihren Angaben verlässt Ihr Gerät. Es gibt keinen Server, "
        + "keine Anmeldung und keine Speicherung."}),
      el("div", {class:"reihe"}, [
        el("button", {class:"knopf", id:"los", text:"Einstufung beginnen"}),
      ]),
    ]),
    el("div", {class:"karte"}, [
      el("h2", {text:"Woher die Fragen kommen"}),
      el("p", {id:"herkunft"}),
    ]),
  );
  document.getElementById("los").onclick = () => { schritt = 0; verlauf = []; antworten = {}; zeichnen(); };
  const z = d.d.zahlen;
  document.getElementById("herkunft").textContent =
    `${z.fragen} Fragen, ${z.ausschluesse} ausdrückliche Ausschlüsse und ${z.beispiele} amtliche `
    + `Beispiele, Zeile für Zeile aus dem Verordnungstext und dem Entwurf der Leitlinien der `
    + `Europäischen Kommission vom 19. Mai 2026 — 148 Seiten zu Anhang III, 13 Seiten zu Anhang I.`;
  document.getElementById("stand").textContent = "Stand der Daten: " + (d.d.stand || "—");
}

function bereichsname(frage) {
  const b = (d.aufbau.bereiche || []).find((x) => frage.fundstelle.startsWith(x.fundstelle));
  return b ? b.titel : frage.titel || "";
}

function zeichnen() {
  const gruppe = d.naechsteGruppe(antworten);
  if (!gruppe.length) return befundZeigen();
  schritt += 1;
  const gesamt = Math.max(schritt + 1, 6);
  const anteil = Math.min(95, Math.round((schritt / gesamt) * 100));

  const kopf = el("div", {class:"schritt"}, [
    el("span", {text:`Schritt ${schritt}`}),
    el("div", {class:"balken"}, el("i", {style:`width:${anteil}%`})),
    el("span", {text:gruppe.length === 1 ? "eine Frage" : `${gruppe.length} Fragen`}),
  ]);

  const karte = el("div", {class:"karte"});
  const erste = gruppe[0];
  let ueberschrift = "Zu Ihrem System";
  if (erste.stufe === "vorfrage") ueberschrift = "Zuerst drei Fragen zum System selbst";
  else if (erste.stufe === "bereich") ueberschrift = "Womit hat Ihr System zu tun?";
  else if (erste.kennung.startsWith("haupt:")) ueberschrift = bereichsname(erste) || "Genauer nachgefragt";
  else if (erste.kennung.startsWith("anhang-i-gattung:")) ueberschrift = "Um welches Produkt geht es?";
  else if (erste.stufe === "anhang_i") ueberschrift = "Zum Produkt und zur Prüfung";
  else if (erste.stufe === "filter") ueberschrift = "Ausnahme nach Artikel 6 Absatz 3";
  else ueberschrift = bereichsname(erste) || "Zu Ihrem System";
  karte.append(el("h2", {text:ueberschrift}));
  if (erste.stufe === "bereich") {
    karte.append(el("p", {class:"leise", text:"Mehrfachnennung möglich. Was nicht zutrifft, "
      + "bitte mit Nein beantworten — der Helfer fragt dann nicht weiter danach. "
      + "Diese acht Sätze sortieren nur; entschieden wird danach."}));
  }

  let letzterBereich = null;
  for (const f of gruppe) {
    if (f.kennung.startsWith("haupt:")) {
      const b = bereichsname(f);
      if (b && b !== letzterBereich) {
        karte.append(el("p", {class:"leise", style:"margin:1.2rem 0 .2rem;font-weight:500", text:b}));
        letzterBereich = b;
      }
    }
    const zeile = el("div", {class:"frage"});
    zeile.append(el("p", {class:"fragetext", text:f.text}));
    const wahl = el("div", {class:"wahl"});
    for (const [wert, wort] of [[true,"Ja"],[false,"Nein"],[TRIFFT_NICHT_ZU,"Trifft nicht zu"]]) {
      const b = el("button", {type:"button", "aria-pressed":"false", text:wort});
      b.onclick = () => {
        antworten[f.kennung] = wert;
        for (const g of wahl.children) g.setAttribute("aria-pressed","false");
        b.setAttribute("aria-pressed","true");
        pruefeWeiter();
      };
      wahl.append(b);
    }
    zeile.append(wahl);
    if (f.beleg) zeile.append(el("p", {class:"beleg", text:"Leitlinien der Kommission, Absatz " + f.beleg}));
    if (f.wirkung) zeile.append(el("p", {class:"beleg", text:f.wirkung}));
    karte.append(zeile);
  }

  const weiter = el("button", {class:"knopf", id:"weiter", text:"Weiter", disabled:""});
  weiter.onclick = () => { verlauf.push({...antworten}); zeichnen(); };
  const zurueck = el("button", {class:"knopf leer", text:"Zurück"});
  zurueck.onclick = () => {
    if (!verlauf.length) { schritt = 0; return start(); }
    antworten = verlauf.pop(); schritt = Math.max(0, schritt - 2); zeichnen();
  };
  karte.append(el("div", {class:"reihe"}, [weiter, zurueck]));
  buehne.replaceChildren(kopf, karte);
  window.scrollTo({top:0, behavior:"instant"});

  function pruefeWeiter() {
    const fertig = gruppe.every((f) => antworten[f.kennung] !== undefined);
    const w = document.getElementById("weiter");
    if (fertig) w.removeAttribute("disabled"); else w.setAttribute("disabled","");
  }
}

function befundZeigen() {
  const e = d.ergebnis(antworten);
  const k = KLASSEN[e.klasse] || KLASSEN.kein_hohes_risiko;
  const kasten = el("div", {class:"befund " + k.stil}, [
    el("div", {class:"zeichen", text:k.zeichen + " " + k.wort}),
    el("h2", {text:k.wort}),
    el("p", {text:e.endtext || k.satz}),
  ]);

  const karte = el("div", {class:"karte"});
  let etwasDrin = false;
  if (e.getroffene_punkte.length) {
    etwasDrin = true;
    const liste = el("dl");
    for (const p of e.getroffene_punkte) {
      liste.append(el("dt", {text:p.titel || p.bereich}));
      liste.append(el("dd", {class:"stelle", text:p.fundstelle.replace("KI-VO/anh-III/nr-","Anhang III Nummer ").replace("KI-VO/anh-I","Anhang I").replace(/-([a-e])$/," Buchstabe $1")}));
      liste.append(el("dd", {class:"leise", text:p.hauptfrage.text}));
    }
    karte.append(el("h2", {text:"Die Stelle, auf der das beruht"}), liste);
  }
  if (e.filter_greift) {
    etwasDrin = true;
    karte.append(el("h2", {text:"Welche Ausnahme greift"}), el("p", {text:e.filter_grund}));
  }
  if (!etwasDrin) {
    // Ohne getroffene Stelle gibt es nichts zu zeigen. Eine leere Karte wäre
    // ein Kasten, der nichts sagt — der Nutzer sucht dann, was ihm entgeht.
    etwasDrin = true;
    karte.append(
      el("h2", {text:"Was jetzt gilt"}),
      el("p", {text:"Es bleibt die Pflicht zur KI-Kompetenz nach Artikel 4: wer KI einsetzt oder "
        + "anbietet, muss dafür sorgen, dass die damit befassten Personen sie verstehen. "
        + "Werden personenbezogene Daten verarbeitet, gilt daneben die Datenschutz-Grundverordnung."}),
      el("p", {class:"leise", text:"Ändert sich der Zweck des Systems, ändert sich die Einstufung. "
        + "Dann lohnt ein neuer Durchlauf."}),
    );
  }
  if (e.belege.length) {
    karte.append(el("p", {class:"beleg", text:"Leitlinien der Kommission, Absätze "
      + e.belege.join(", ")}));
  }

  const beispiele = el("div");
  for (const p of e.getroffene_punkte) {
    if (!p.beispiele.length) continue;
    const auf = el("details");
    auf.append(el("summary", {text:`${p.beispiele.length} amtliche Beispiele zu dieser Stelle`}));
    for (const b of p.beispiele) {
      const ja = b.wertung === "hochrisiko";
      auf.append(el("div", {class:"beispiel"}, [
        el("div", {class:"wertung " + (ja ? "ja" : "nein"),
          text:ja ? "▲ erfasst" : "● nicht erfasst"}),
        el("p", {text:b.lage}),
        b.begruendung ? el("p", {class:"leise", text:b.begruendung}) : null,
        b.beleg ? el("p", {class:"beleg", text:"Absatz " + b.beleg}) : null,
      ]));
    }
    beispiele.append(auf);
  }

  const nochmal = el("button", {class:"knopf leer", text:"Von vorn"});
  nochmal.onclick = () => { antworten = {}; schritt = 0; verlauf = []; start(); };
  buehne.replaceChildren(kasten, karte, beispiele,
    el("div", {class:"reihe"}, [nochmal]));
  window.scrollTo({top:0, behavior:"instant"});
}

fetch("./fragefolge.json")
  .then((r) => r.json())
  .then((daten) => { d = new Durchlauf(daten); start(); })
  .catch(() => {
    buehne.replaceChildren(el("div", {class:"karte"}, el("p", {
      text:"Die Fragedaten konnten nicht geladen werden. Die Seite braucht die Datei "
        + "fragefolge.json im selben Ordner."})));
  });
