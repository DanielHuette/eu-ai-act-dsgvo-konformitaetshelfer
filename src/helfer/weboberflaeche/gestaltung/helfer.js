/* Die Oberfläche spricht mit der eigenen Schnittstelle — sonst mit niemandem.
 *
 * Kein Framework, kein Nachladen, keine Adresse außerhalb dieses Dienstes.
 * Das ist keine Sparsamkeit, sondern Teil des Zwecks: das Werkzeug muss in
 * einem Haus ohne Internetzugang laufen, und was jemand über sein KI-System
 * eintippt, darf den Rechner nicht verlassen.
 *
 * Der Knopf "Prüfen" schickt zwei Anfragen:
 *
 *   POST /api/einstufung  — die Einstufung. Sie entsteht ohne Sprachmodell und
 *                           kennt die genauen Angaben aus dem Fragebogen. Sie
 *                           ist die verbindliche Aussage der Seite.
 *   POST /api/frage       — die Auskunft im Zusammenhang samt Fundstellen und
 *                           dem Lernhinweis aus dem passenden Anwendungsfall.
 *
 * Getrennt, weil die Einstufung auch dann steht, wenn kein Sprachmodell
 * erreichbar ist. Fällt die zweite Anfrage aus, bleibt die erste sichtbar.
 *
 * Alle Texte werden über textContent gesetzt, nie über innerHTML: der
 * Gesetzestext und die eigene Beschreibung sollen als Text erscheinen, nicht
 * als Anweisung an den Browser.
 */
"use strict";

const form = document.getElementById("pruefform");
const knopf = document.getElementById("pruefknopf");
const laufhinweis = document.getElementById("laufhinweis");
const ergebnis = document.getElementById("ergebnis");
const fehlerbereich = document.getElementById("fehlerbereich");

/* ------------------------------------------------------------- Werkzeuge */

function bauen(tag, klasse, text) {
  const knoten = document.createElement(tag);
  if (klasse) { knoten.className = klasse; }
  if (text !== undefined && text !== null && text !== "") { knoten.textContent = text; }
  return knoten;
}

function leeren(knoten) {
  while (knoten.firstChild) { knoten.removeChild(knoten.firstChild); }
}

function datumDeutsch(iso) {
  if (!iso) { return ""; }
  const teile = String(iso).split("-");
  if (teile.length !== 3) { return String(iso); }
  return teile[2] + "." + teile[1] + "." + teile[0];
}

function fehlerZeigen(satz, hinweis) {
  document.getElementById("fehlertext").textContent = satz;
  document.getElementById("fehlerhinweis").textContent = hinweis || "";
  fehlerbereich.hidden = false;
  fehlerbereich.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* Eine Anfrage an die eigene Schnittstelle. Fehler kommen als deutscher Satz
 * zurück — das Feld heißt "fehler". Kommt etwas anderes, wird daraus ein
 * eigener Satz gemacht, damit nie eine englische Rohmeldung erscheint. */
async function schicken(weg, inhalt) {
  let antwort;
  try {
    antwort = await fetch(weg, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(inhalt)
    });
  } catch (stoerung) {
    throw new Error("Der Dienst ist nicht erreichbar. Läuft er noch?");
  }
  let daten = null;
  try { daten = await antwort.json(); } catch (stoerung) { daten = null; }
  if (!antwort.ok) {
    const satz = (daten && daten.fehler)
      ? daten.fehler
      : "Der Dienst hat mit Fehlercode " + antwort.status + " geantwortet.";
    const fehler = new Error(satz);
    fehler.hinweis = (daten && daten.hinweis) || "";
    throw fehler;
  }
  return daten;
}

/* ------------------------------------------------------- Eingaben sammeln */

/* Liest den Fragebogen aus. "Weiß ich nicht" ist der leere Wert und wird nicht
 * mitgeschickt — ein nicht gesendetes Merkmal wird zur offenen Frage, ein
 * gesendetes "nein" ist eine Aussage. Der Unterschied entscheidet über die
 * Einstufung und darf nicht verwischen. */
function merkmaleSammeln() {
  const merkmale = {};
  const rollen = [];
  document.querySelectorAll('#pruefform .punkt').forEach(function (punkt) {
    const kennung = punkt.dataset.kennung;
    const art = punkt.dataset.art;
    if (art === "auswahl") { return; }
    if (art === "ja_nein") {
      const gewaehlt = punkt.querySelector('input[type="radio"]:checked');
      if (gewaehlt && gewaehlt.value !== "") { merkmale[kennung] = gewaehlt.value; }
      return;
    }
    const feld = punkt.querySelector('input[type="text"]');
    if (feld && feld.value.trim() !== "") { merkmale[kennung] = feld.value.trim(); }
  });
  document.querySelectorAll('#pruefform input[name="rollen"]:checked')
    .forEach(function (kasten) { rollen.push(kasten.value); });
  return { merkmale: merkmale, rollen: rollen };
}

/* ----------------------------------------------------------- Risikokarte */

/* Welche Farbgruppe zu welcher Klasse gehört. Die Farbe ist die Zugabe; das
 * Wort in der Marke trägt die Aussage. */
const KARTENKLASSE = {
  verboten: "k-verboten",
  hochrisiko_anhang_i: "k-hoch",
  hochrisiko_anhang_iii: "k-hoch",
  hochrisiko_ausnahme: "k-hoch",
  gpai_systemisch: "k-transparenz",
  gpai: "k-transparenz",
  transparenz: "k-transparenz",
  minimal: "k-minimal",
  unklar: ""
};

const KARTENMARKE = {
  verboten: "✕ Verboten",
  hochrisiko_anhang_i: "▲ Hohes Risiko",
  hochrisiko_anhang_iii: "▲ Hohes Risiko",
  hochrisiko_ausnahme: "▲ Hohes Risiko, Ausnahme möglich",
  gpai_systemisch: "● Modell mit systemischem Risiko",
  gpai: "● Modell mit allgemeinem Verwendungszweck",
  transparenz: "● Transparenzpflichten",
  minimal: "✓ Geringes Risiko",
  unklar: "? Nicht eindeutig"
};

const KARTENTITEL = {
  verboten: "Dieses System darf so nicht betrieben werden",
  hochrisiko_anhang_i: "Hochrisiko-System über das Produktsicherheitsrecht",
  hochrisiko_anhang_iii: "Hochrisiko-System über den Einsatzbereich",
  hochrisiko_ausnahme: "Hochrisiko-Bereich, aber eine Ausnahme kann greifen",
  gpai_systemisch: "Modell mit allgemeinem Verwendungszweck und systemischem Risiko",
  gpai: "Modell mit allgemeinem Verwendungszweck",
  transparenz: "Es gelten Transparenzpflichten",
  minimal: "Keine besonderen Pflichten außer KI-Kompetenz",
  unklar: "Für eine Einstufung fehlen Angaben"
};

function karteZeichnen(kennung, klartext, rollen) {
  const karte = document.getElementById("karte");
  karte.className = "risikokarte " + (KARTENKLASSE[kennung] || "");
  document.getElementById("kartenmarke").textContent =
    KARTENMARKE[kennung] || kennung;
  document.getElementById("kartentitel").textContent =
    KARTENTITEL[kennung] || kennung;
  document.getElementById("kartentext").textContent = klartext || "";

  const zeile = document.getElementById("kartenrollen");
  if (rollen && rollen.length) {
    zeile.textContent = "Ihre Rolle: " + rollen.map(function (r) {
      return r.kennung + " — " + r.klartext;
    }).join(" · ");
  } else {
    zeile.textContent = "Ihre Rolle ist noch nicht angegeben. Die Auskunft "
      + "nennt deshalb die Pflichten für Anbieter und für Betreiber.";
  }
}

/* ---------------------------------------------------------- Begründungen */

const SICHERHEITSWORT = {
  sicher: "sicher",
  wahrscheinlich: "wahrscheinlich",
  zu_pruefen: "noch zu prüfen"
};

function begruendungZeichnen(hinweise) {
  const ziel = document.getElementById("begruendung");
  leeren(ziel);
  if (!hinweise || !hinweise.length) {
    ziel.appendChild(bauen("p", "erlaeuterung", "Keine Begründung vorhanden."));
    return;
  }
  hinweise.forEach(function (hinweis) {
    const kasten = bauen("div", "grund");
    const satz = bauen("p", null, hinweis.begruendung);
    const marke = bauen("span", "sicherheit s-" + hinweis.sicherheit,
      SICHERHEITSWORT[hinweis.sicherheit] || hinweis.sicherheit);
    satz.appendChild(document.createTextNode(" "));
    satz.appendChild(marke);
    kasten.appendChild(satz);
    if (hinweis.rechtsgrundlage && hinweis.rechtsgrundlage.length) {
      kasten.appendChild(bauen("p", "fundstelle",
        "Fundstellen: " + hinweis.rechtsgrundlage.join(", ")));
    }
    ziel.appendChild(kasten);
  });
}

/* ------------------------------------------------------------- Pflichten */

function pflichtenZeichnen(zielkennung, pflichten) {
  const ziel = document.getElementById(zielkennung);
  leeren(ziel);
  if (!pflichten || !pflichten.length) {
    ziel.appendChild(bauen("p", "erlaeuterung",
      "Für diese Einstufung sind im Regelsatz keine Pflichten verzeichnet."));
    return 0;
  }
  const heute = new Date().toISOString().slice(0, 10);
  pflichten.forEach(function (pflicht, nummer) {
    const zeile = bauen("div", "pflicht");

    const kasten = document.createElement("input");
    kasten.type = "checkbox";
    kasten.id = zielkennung + "-" + nummer;
    /* Nur in diesem Fenster: es wird nichts gespeichert. Wer die Liste
     * behalten will, druckt die Seite — das steht im Hinweis darüber. */
    zeile.appendChild(kasten);

    const inhalt = bauen("div", "pflicht-inhalt");
    const titel = bauen("label",
      "pflicht-titel" + (pflicht.schwere && pflicht.schwere !== "pflicht"
        ? " schwere-" + pflicht.schwere : ""),
      pflicht.titel);
    titel.setAttribute("for", kasten.id);
    inhalt.appendChild(titel);
    inhalt.appendChild(bauen("p", "pflicht-tun", pflicht.was_zu_tun_ist));

    const unten = bauen("div", "pflicht-zeile");
    unten.appendChild(bauen("span", "fundstelle", pflicht.fundstellen_text));
    if (pflicht.gilt_ab) {
      const kommt = pflicht.gilt_ab > heute;
      unten.appendChild(bauen("span", "frist" + (kommt ? " offen" : ""),
        (kommt ? "gilt ab " : "gilt seit ") + datumDeutsch(pflicht.gilt_ab)));
    }
    if (pflicht.nachweis) {
      unten.appendChild(bauen("span", null, "Nachweis: " + pflicht.nachweis));
    }
    inhalt.appendChild(unten);
    if (pflicht.bei_verstoss) {
      inhalt.appendChild(bauen("p", "fundstelle",
        "Bei Verstoß: " + pflicht.bei_verstoss));
    }
    zeile.appendChild(inhalt);
    ziel.appendChild(zeile);
  });
  return pflichten.length;
}

/* ---------------------------------------------------------------- Belege */

function belegeZeichnen(belege) {
  const ziel = document.getElementById("belege");
  leeren(ziel);
  if (!belege || !belege.length) {
    ziel.appendChild(bauen("p", "erlaeuterung",
      "Zu dieser Frage wurde im Bestand keine Stelle gefunden."));
    return;
  }
  belege.forEach(function (beleg, nummer) {
    const kasten = bauen("details", "beleg");
    /* Die erste Stelle steht offen: wer prüft, soll gleich etwas lesen. */
    if (nummer === 0) { kasten.open = true; }
    const griff = document.createElement("summary");
    griff.appendChild(bauen("span", "beleg-kopf", beleg.fundstelle));
    if (beleg.titel) {
      griff.appendChild(document.createTextNode(" "));
      griff.appendChild(bauen("span", "beleg-titel", "— " + beleg.titel));
    }
    kasten.appendChild(griff);
    kasten.appendChild(bauen("div", "wortlaut", beleg.auszug));
    kasten.appendChild(bauen("p", "wege",
      "Gefunden über: " + (beleg.wege || []).join(", ")
      + " · Kennung " + beleg.kennung));
    ziel.appendChild(kasten);
  });
}

/* --------------------------------------------------------------- Fristen */

let fristenGeladen = false;

async function fristenZeichnen() {
  if (fristenGeladen) { return; }
  const ziel = document.getElementById("fristen");
  let daten;
  try {
    const antwort = await fetch("/api/fristen");
    if (!antwort.ok) { throw new Error("Fehlercode " + antwort.status); }
    daten = await antwort.json();
  } catch (stoerung) {
    leeren(ziel);
    ziel.appendChild(bauen("p", "erlaeuterung",
      "Die Geltungsdaten konnten nicht geladen werden."));
    return;
  }
  leeren(ziel);
  const liste = bauen("ul", "fristen");
  daten.stufen.forEach(function (stufe) {
    const zeile = bauen("li", "fristzeile " + (stufe.schon_in_kraft ? "gilt" : "kommt"));
    zeile.appendChild(bauen("span", "fristdatum", datumDeutsch(stufe.datum)));
    zeile.appendChild(bauen("span", "fristmarke",
      stufe.schon_in_kraft ? "gilt" : "kommt"));
    zeile.appendChild(bauen("span", null, stufe.was));
    liste.appendChild(zeile);
  });
  ziel.appendChild(liste);
  ziel.appendChild(bauen("p", "fundstelle", "Fundstelle: " + daten.fundstelle));
  if (daten.vorbehalt) {
    ziel.appendChild(bauen("p", "vorbehalt", daten.vorbehalt));
  }
  fristenGeladen = true;
}

/* ------------------------------------------------------------ Offene Fragen */

function fragenZeichnen(fragen) {
  const block = document.getElementById("fragenblock");
  const liste = document.getElementById("offenefragen");
  leeren(liste);
  if (!fragen || !fragen.length) { block.hidden = true; return; }
  fragen.forEach(function (frage) { liste.appendChild(bauen("li", null, frage)); });
  block.hidden = false;
}

/* ------------------------------------------------------------------ Lauf */

async function pruefen() {
  fehlerbereich.hidden = true;
  const beschreibung = document.getElementById("beschreibung").value.trim();
  const frage = document.getElementById("frage").value.trim();

  if (!beschreibung && !frage) {
    fehlerZeigen("Bitte beschreiben Sie Ihr KI-System oder stellen Sie eine Frage.",
      "Ohne Angaben kann nicht eingestuft werden.");
    return;
  }

  const gesammelt = merkmaleSammeln();
  knopf.disabled = true;
  laufhinweis.textContent = "Wird geprüft …";

  try {
    const einstufungsantwort = await schicken("/api/einstufung", {
      beschreibung: beschreibung || frage,
      rollen: gesammelt.rollen,
      merkmale: gesammelt.merkmale
    });

    const e = einstufungsantwort.einstufung;
    karteZeichnen(einstufungsantwort.schwerste_klasse,
      einstufungsantwort.schwerste_klartext,
      einstufungsantwort.rollen_klartext);
    begruendungZeichnen(e.hinweise);
    pflichtenZeichnen("pflichten", e.pflichten);
    const anzahlDatenschutz = pflichtenZeichnen("datenschutz", e.datenschutz);
    document.getElementById("datenschutzblock").hidden = !anzahlDatenschutz;
    fragenZeichnen(e.offene_fragen);

    if (einstufungsantwort.nicht_erkannte_merkmale
        && einstufungsantwort.nicht_erkannte_merkmale.length) {
      fehlerZeigen("Einige Angaben wurden nicht ausgewertet: "
        + einstufungsantwort.nicht_erkannte_merkmale.join(", ") + ".",
        "Die Einstufung steht, aber diese Angaben sind nicht eingegangen.");
    }

    ergebnis.hidden = false;
    laufhinweis.textContent = "Einstufung steht. Auskunft wird formuliert …";
    fristenZeichnen();

    /* Zweiter Teil. Scheitert er, bleibt die Einstufung oben stehen — sie ist
     * der Teil, auf den man sich verlassen kann. */
    const auskunft = await schicken("/api/frage", {
      frage: frage || "Welche Pflichten gelten für dieses KI-System?",
      beschreibung: beschreibung
    });
    const a = auskunft.antwort;
    document.getElementById("auskunft").textContent = a.text;
    document.getElementById("auskunftquelle").textContent = a.ohne_modell
      ? "Aus dem Regelwerk zusammengestellt, ohne Sprachmodell."
      : "Formuliert durch " + a.modell + ". Die Einstufung oben entsteht ohne "
        + "Sprachmodell und ist davon unberührt.";
    belegeZeichnen(a.belege);

    const lernblock = document.getElementById("lernblock");
    if (a.lernhinweis) {
      document.getElementById("lernhinweis").textContent = a.lernhinweis;
      document.getElementById("beispielfaelle").textContent =
        (a.beispielfaelle && a.beispielfaelle.length)
          ? "Vergleichbare Fälle im Bestand: " + a.beispielfaelle.join(" · ")
          : "";
      lernblock.hidden = false;
    } else {
      lernblock.hidden = true;
    }

    if (a.warnungen && a.warnungen.length) {
      fehlerZeigen(a.warnungen[0], a.warnungen.slice(1).join(" "));
    }
    laufhinweis.textContent = "Fertig in " + (auskunft.dauer_ms || 0)
      + " Millisekunden.";
    document.getElementById("karte").scrollIntoView(
      { behavior: "smooth", block: "start" });

  } catch (fehler) {
    fehlerZeigen(fehler.message, fehler.hinweis);
    laufhinweis.textContent = "";
  } finally {
    knopf.disabled = false;
  }
}

form.addEventListener("submit", function (ereignis) {
  ereignis.preventDefault();
  pruefen();
});

/* Zeichenzähler: wer über die Grenze schreibt, soll es vorher sehen und nicht
 * erst, wenn der Dienst ablehnt. */
const beschreibungsfeld = document.getElementById("beschreibung");
const zeichenzahl = document.getElementById("zeichenzahl");
function zaehlen() {
  zeichenzahl.textContent = String(beschreibungsfeld.value.length);
}
beschreibungsfeld.addEventListener("input", zaehlen);
zaehlen();
