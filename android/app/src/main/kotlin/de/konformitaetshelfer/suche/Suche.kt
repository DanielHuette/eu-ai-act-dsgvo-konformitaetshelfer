package de.konformitaetshelfer.suche

import de.konformitaetshelfer.daten.Rechtsbestand
import de.konformitaetshelfer.daten.Treffer

/**
 * Die Suche im Rechtsbestand.
 *
 * Drei Wege, ein Ergebnis:
 *  - FUNDSTELLE: Nennt die Frage "Artikel 6 Absatz 3", wird genau die Stelle
 *    geholt. Das ist keine Schätzung, sondern eine Tatsache, und wiegt
 *    deshalb dreifach.
 *  - STICHWORT: FTS5 mit bm25. Findet, was wörtlich dasteht.
 *  - VEKTOR: Kosinusmaß über die eingebetteten Einheiten. Findet, was
 *    dasselbe meint, aber anders heißt - "Bewerber aussortieren" findet
 *    "Auswahl natürlicher Personen".
 *
 * Zusammengeführt wird über die Rangfusion mit 1/(60+Rang), wie im
 * Python-Teil des Werkzeugs. Addiert werden Rangplätze und nicht Punktzahlen:
 * bm25 und Kosinusmaß haben verschiedene Maßstäbe, ihre Zahlen zu addieren
 * wäre das Addieren von Metern und Kilogramm.
 *
 * Fehlt das Einbettungsmodell, läuft die Suche über zwei Wege weiter. Sie
 * sagt das nicht an - was das Werkzeug kann, soll am Ergebnis ablesbar sein
 * und nicht an einer Betriebsmeldung.
 */
class Suche(
    private val bestand: Rechtsbestand,
    private val einbetter: Einbetter?,
    private val vorsilbeFrage: String,
    private val dimensionen: Int,
) {

    /** Einmal geladen und behalten: 1972 mal 384 Zahlen sind rund 3 MB. */
    private val vektoren by lazy {
        if (einbetter == null) null else bestand.alleVektoren(dimensionen)
    }

    fun suchen(frage: String, anzahl: Int = 8): List<Treffer> {
        val wege = HashMap<String, List<Int>>(3)

        val genannte = Fundstellen.ausFrage(frage).mapNotNull {
            bestand.einheitNachKennung(it)?.nummer
        }
        if (genannte.isNotEmpty()) wege[WEG_FUNDSTELLE] = genannte.distinct()

        val abfrage = Stichwortabfrage.bauen(frage)
        if (abfrage.isNotEmpty()) {
            wege[WEG_STICHWORT] = bestand.stichwortsuche(abfrage, JE_WEG)
        }

        // In eine örtliche Größe gefasst: die Nicht-Null-Prüfung einer
        // Eigenschaft trägt nicht in den Lambda-Ausdruck hinein.
        val einbetterJetzt = einbetter
        val block = vektoren
        if (einbetterJetzt != null && block != null) {
            val gefragt = runCatching {
                einbetterJetzt.einbetten(frage, vorsilbeFrage)
            }.getOrNull()
            if (gefragt != null && gefragt.size == dimensionen) {
                wege[WEG_VEKTOR] = Kosinus.naechste(gefragt, block, JE_WEG).map { it.first }
            }
        }

        val verschmolzen = Rangfusion.verschmelzen(wege, GEWICHTE)
        if (verschmolzen.isEmpty()) return emptyList()

        val vorne = verschmolzen.take(anzahl)
        val einheiten = bestand.einheitenNachNummern(vorne.map { it.nummer })
        return vorne.mapNotNull { platz ->
            einheiten[platz.nummer]?.let {
                Treffer(einheit = it, punktzahl = platz.punktzahl, wege = platz.wege)
            }
        }
    }

    companion object {
        const val WEG_FUNDSTELLE = "fundstelle"
        const val WEG_STICHWORT = "stichwort"
        const val WEG_VEKTOR = "vektor"

        /** So viele Treffer liefert jeder Weg in die Fusion. */
        const val JE_WEG = 50

        /**
         * Der Fundstellenweg wiegt dreifach: wer eine Stelle nennt, will sie
         * sehen, und das ist keine Ähnlichkeitsschätzung.
         */
        val GEWICHTE = mapOf(
            WEG_FUNDSTELLE to 3.0,
            WEG_STICHWORT to 1.0,
            WEG_VEKTOR to 1.0,
        )
    }
}

/** Ein Platz in der verschmolzenen Liste. */
data class Fusionsplatz(val nummer: Int, val punktzahl: Double, val wege: Set<String>)

/**
 * Die Rangfusion.
 *
 * Reine Rechnung ohne Datenbank, damit sie prüfbar ist.
 */
object Rangfusion {

    /**
     * Die Konstante der Rangfusion. 60 ist der in der Literatur gebräuchliche
     * Wert; er dämpft die Spitze, damit ein einzelner Weg die Liste nicht
     * allein bestimmt.
     */
    const val K = 60.0

    fun verschmelzen(
        wege: Map<String, List<Int>>,
        gewichte: Map<String, Double>,
        k: Double = K,
    ): List<Fusionsplatz> {
        val summe = HashMap<Int, Double>()
        val herkunft = HashMap<Int, MutableSet<String>>()
        for ((name, liste) in wege) {
            val gewicht = gewichte[name] ?: 1.0
            liste.forEachIndexed { stelle, nummer ->
                val rang = stelle + 1
                summe[nummer] = (summe[nummer] ?: 0.0) + gewicht / (k + rang)
                herkunft.getOrPut(nummer) { LinkedHashSet() }.add(name)
            }
        }
        return summe.entries
            .map { Fusionsplatz(it.key, it.value, herkunft[it.key] ?: emptySet()) }
            .sortedWith(compareByDescending<Fusionsplatz> { it.punktzahl }.thenBy { it.nummer })
    }
}

/**
 * Erkennt genannte Fundstellen und übersetzt sie in Kennungen des Bestands.
 *
 * Gleiche Form wie im Python-Teil: "Art. 6 Abs. 3" wird zu "KI-VO/art-6/abs-3".
 * Welcher Rechtsakt gemeint ist, verrät meist die Frage selbst; fehlt der
 * Hinweis, werden beide Kennungen geliefert und die Suche entscheidet.
 */
object Fundstellen {

    private val MUSTER = Regex(
        "(?:(?:Art(?:ikel)?\\.?)\\s*(\\d{1,3})" +
            "(?:\\s*(?:Abs(?:atz)?\\.?)\\s*(\\d{1,2}))?" +
            "(?:\\s*(?:Buchst(?:abe)?\\.?)\\s*([a-z]))?" +
            "|(?:§)\\s*(\\d{1,3}[a-z]?)" +
            "|(?:Anhang)\\s*([IVXLC]+)(?:\\s*(?:Nr\\.?|Nummer)\\s*(\\d{1,2}))?" +
            "|(?:Erw(?:ägungsgrund|aegungsgrund|G)?\\.?)\\s*(\\d{1,3}))",
        RegexOption.IGNORE_CASE,
    )

    fun ausFrage(frage: String): List<String> {
        val flach = frage.lowercase()
        val akte = when {
            "bdsg" in flach || "bundesdatenschutz" in flach -> listOf("BDSG")
            listOf("dsgvo", "datenschutz-grundverordnung", "gdpr").any { it in flach } ->
                listOf("DSGVO")
            listOf("ki-vo", "ki-verordnung", "ai act", "ai-act", "künstliche intelligenz",
                "kuenstliche intelligenz").any { it in flach } -> listOf("KI-VO")
            else -> listOf("KI-VO", "DSGVO")
        }

        val kennungen = ArrayList<String>()
        for (treffer in MUSTER.findAll(frage)) {
            val g = treffer.groupValues
            when {
                g[1].isNotEmpty() -> for (akt in akte) {
                    var stamm = "$akt/art-${g[1]}"
                    if (g[2].isNotEmpty()) {
                        stamm += "/abs-${g[2]}"
                        if (g[3].isNotEmpty()) stamm += "-${g[3].lowercase()}"
                    }
                    kennungen.add(stamm)
                }
                g[4].isNotEmpty() -> kennungen.add("BDSG/par-${g[4]}")
                g[5].isNotEmpty() -> {
                    var stamm = "KI-VO/anh-${g[5].uppercase()}"
                    if (g[6].isNotEmpty()) stamm += "/nr-${g[6]}"
                    kennungen.add(stamm)
                }
                g[7].isNotEmpty() -> for (akt in akte) kennungen.add("$akt/erw-${g[7]}")
            }
        }
        return kennungen.distinct()
    }
}

/**
 * Baut die FTS5-Abfrage aus einer Frage in gewöhnlichen Worten.
 *
 * Zwei Dinge erledigt sie, die man leicht übersieht:
 *
 * 1. ENTSCHÄRFEN. In FTS5 sind Anführungszeichen, Sternchen, Klammern und
 *    die Wörter AND, OR, NOT und NEAR Befehle. Eine Frage, die sie enthält,
 *    würde die Abfrage zerlegen oder abbrechen. Jedes Wort wandert deshalb
 *    in Anführungszeichen, und innenliegende werden verdoppelt.
 *
 * 2. UMLAUTE IN BEIDEN SCHREIBWEISEN. Der Zerteiler der Datenbank ist mit
 *    remove_diacritics=2 gebaut; im Index steht "beschaftigte", nicht
 *    "beschäftigte". Wer "Beschaeftigte" mit ae tippt, würde ohne Zutun
 *    nichts finden. Also wird jedes Wort zusätzlich in der Form mit
 *    aufgelöstem Umlaut gefragt.
 */
object Stichwortabfrage {

    /**
     * Deutsche Füllwörter. Sie stehen in jedem Rechtstext und unterscheiden
     * nichts - in der Stichwortsuche würden sie alles gleich machen.
     */
    private val FUELLWOERTER: Set<String> = (
        "aber alle allem allen aller alles als also am an ander andere anderem anderen " +
            "anderer anderes auch auf aus bei beim bin bis bist da damit dann der den des " +
            "dem die das dass dein deine dessen deshalb dies diese diesem diesen dieser " +
            "dieses doch dort du durch ein eine einem einen einer eines er es euer euch " +
            "fur gegen gewesen hab habe haben hat hatte hatten hier hin hinter ich ihr " +
            "ihre ihrem ihren ihrer ihres im in indem ins ist ja jede jedem jeden jeder " +
            "jedes jener jene kann kein keine keinem keinen keiner man mehr mein meine " +
            "mit nach nicht nichts noch nun nur ob oder ohne sein seine seinem seinen " +
            "seiner sich sie sind so solche solchem solchen soll sollen sondern sonst " +
            "uber um und uns unser unsere unter vom von vor wahrend war waren was weil " +
            "welche welchem welchen welcher welches wenn wer werde werden wie wieder will " +
            "wir wird wirst wo wollen wurde wurden zu zum zur zwar zwischen"
        ).split(" ").toSet()

    private val WORT = Regex("[\\p{L}\\p{Nd}]+")

    /** Löst Umlaute auf, wie es ein deutscher Schreiber ohne Umlauttaste tut. */
    fun mitAe(wort: String): String = wort
        .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        .replace("ß", "ss")

    /** Wie der Zerteiler der Datenbank faltet: Umlaut zum Grundbuchstaben. */
    fun wieImIndex(wort: String): String = wort
        .replace("ä", "a").replace("ö", "o").replace("ü", "u")
        .replace("ß", "ss")

    fun bauen(frage: String): String {
        val gesehen = LinkedHashSet<String>()
        for (fund in WORT.findAll(frage.lowercase())) {
            val wort = fund.value
            if (wort.length < 2) continue
            if (wieImIndex(wort) in FUELLWOERTER || mitAe(wort) in FUELLWOERTER) continue
            gesehen.add(wort)
            // Hat der Nutzer ae/oe/ue getippt, steht im Index die Form mit
            // Grundbuchstaben. Beide Formen fragen kostet nichts.
            val gefaltet = wort.replace("ae", "a").replace("oe", "o").replace("ue", "u")
            if (gefaltet != wort && gefaltet.length >= 2) gesehen.add(gefaltet)
        }
        if (gesehen.isEmpty()) return ""
        return gesehen.joinToString(" OR ") { "\"" + it.replace("\"", "\"\"") + "\"" }
    }
}

/**
 * Kosinusmaß über den Vektorblock.
 *
 * Die Reihen im Bestand und die der Frage sind beide auf Länge 1 gebracht;
 * das Skalarprodukt ist deshalb schon das Kosinusmaß.
 */
object Kosinus {

    fun naechste(
        frage: FloatArray,
        block: de.konformitaetshelfer.daten.Vektorblock,
        anzahl: Int,
    ): List<Pair<Int, Float>> {
        val punkte = ArrayList<Pair<Int, Float>>(block.anzahl)
        val d = block.dimensionen
        for (zeile in 0 until block.anzahl) {
            var summe = 0.0f
            val anfang = zeile * d
            for (i in 0 until d) {
                summe += block.werte[anfang + i] * frage[i]
            }
            punkte.add(block.nummern[zeile] to summe)
        }
        return punkte.sortedByDescending { it.second }.take(anzahl)
    }
}
