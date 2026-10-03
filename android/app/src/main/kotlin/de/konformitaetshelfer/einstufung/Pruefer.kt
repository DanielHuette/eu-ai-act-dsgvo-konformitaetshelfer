package de.konformitaetshelfer.einstufung

import de.konformitaetshelfer.daten.Antwort
import de.konformitaetshelfer.daten.Einstufung
import de.konformitaetshelfer.daten.OffeneFrage
import de.konformitaetshelfer.daten.Pflicht
import de.konformitaetshelfer.daten.Risikohinweis
import de.konformitaetshelfer.daten.Risikoklasse
import de.konformitaetshelfer.daten.Risikoregel
import de.konformitaetshelfer.daten.Rolle
import de.konformitaetshelfer.daten.Systembeschreibung

/** Eine Frage, die der Fragebogen stellt. */
data class Frage(
    val feld: String,
    val text: String,
    val fundstelle: String,
    val regel: String,
    /** Überschrift der Gruppe, in der die Frage steht. */
    val gruppe: String,
)

/**
 * Stuft ein KI-System nach der KI-Verordnung ein.
 *
 * HIER UND NUR HIER ENTSTEHT DIE EINSTUFUNG. Ein Sprachmodell wird nie
 * gefragt, ob etwas Hochrisiko ist - es formuliert höchstens das Ergebnis
 * dieser Klasse aus. Der Grund ist nicht Vorsicht, sondern Haftung: eine
 * erfundene Einstufung kostet den Nutzer Geld, und sie wäre nicht
 * nachvollziehbar. Was hier herauskommt, lässt sich bis auf die Regel und
 * die Fundstelle zurückverfolgen.
 *
 * Die Regeln stehen in der Datenbank, nicht in diesem Quelltext. Eine
 * Rechtsänderung ändert daten/regeln/kivo_risikoklassen.yaml und den Export -
 * nicht diese Klasse.
 *
 * Diese Klasse kennt weder Datenbank noch Android. Sie bekommt Regeln und
 * Pflichten als Listen und ist deshalb vollständig prüfbar.
 */
class Pruefer(
    private val regeln: List<Risikoregel>,
    private val pflichten: List<Pflicht>,
) {

    private val nachArt: Map<String, List<Risikoregel>> = regeln.groupBy { it.art }

    // --------------------------------------------------------------- Fragen

    /**
     * Welche Fragen jetzt zu stellen sind.
     *
     * Die Liste wächst mit den Antworten: nach einem Ja bei Anhang III
     * kommen die beiden Fragen zur Ausnahme nach Artikel 6 Absatz 3 dazu,
     * nach einem Ja beim Basismodell die Frage zum systemischen Risiko.
     * Alle 25 Fragen auf einmal zu zeigen, würde niemand beantworten.
     *
     * Die Verbotsfragen erscheinen, wenn die Beschreibung des Nutzers auf sie
     * deutet - oder wenn er sie ausdrücklich anfordert. Ein Verbot zu
     * übersehen, weil die Frage nicht gestellt wurde, ist der schlimmste
     * Fehler, den dieses Werkzeug machen kann; deshalb ist [alleVerbote]
     * jederzeit einschaltbar und die Oberfläche weist darauf hin.
     */
    fun fragen(
        beschreibung: Systembeschreibung,
        alleVerbote: Boolean = false,
    ): List<Frage> {
        val liste = ArrayList<Frage>(32)

        for (regel in nachArt["verbot"].orEmpty()) {
            if (!alleVerbote && !deutetDarauf(regel, beschreibung.beschreibung)) continue
            for (bedingung in regel.bedingungen) {
                liste.add(
                    Frage(
                        feld = bedingung.feld,
                        text = regel.frage.ifBlank { regel.titel },
                        fundstelle = regel.fundstelle,
                        regel = regel.kennung,
                        gruppe = GRUPPE_VERBOT,
                    )
                )
            }
        }

        for (regel in nachArt["hochrisiko_anhang_iii"].orEmpty()) {
            liste.add(
                Frage(
                    feld = regel.kennung,
                    text = regel.frage.ifBlank { regel.titel },
                    fundstelle = regel.fundstelle,
                    regel = regel.kennung,
                    gruppe = GRUPPE_ANHANG_III,
                )
            )
        }

        for (regel in nachArt["hochrisiko_anhang_i"].orEmpty()) {
            for (bedingung in regel.bedingungen) {
                liste.add(
                    Frage(
                        feld = bedingung.feld,
                        text = frageFuerFeld(bedingung.feld, regel.frage),
                        fundstelle = regel.fundstelle,
                        regel = regel.kennung,
                        gruppe = GRUPPE_ANHANG_I,
                    )
                )
            }
        }

        for (regel in nachArt["transparenz"].orEmpty()) {
            for (bedingung in regel.bedingungen) {
                if (liste.any { it.feld == bedingung.feld }) continue
                liste.add(
                    Frage(
                        feld = bedingung.feld,
                        text = frageFuerFeld(bedingung.feld, regel.begruendung),
                        fundstelle = regel.fundstelle,
                        regel = regel.kennung,
                        gruppe = GRUPPE_TRANSPARENZ,
                    )
                )
            }
        }

        for (regel in nachArt["gpai"].orEmpty()) {
            for (bedingung in regel.bedingungen) {
                liste.add(
                    Frage(
                        feld = bedingung.feld,
                        text = regel.frage.ifBlank { regel.titel },
                        fundstelle = regel.fundstelle,
                        regel = regel.kennung,
                        gruppe = GRUPPE_BASISMODELL,
                    )
                )
            }
        }

        // Folgefragen: erst sinnvoll, wenn die Vorfrage mit Ja beantwortet ist.
        if (nachArt["gpai"].orEmpty().any { regel ->
                regel.bedingungen.any { beschreibung.antwort(it.feld) == Antwort.JA }
            }
        ) {
            nachArt["gpai_systemisch"].orEmpty().firstOrNull()?.let { regel ->
                liste.add(
                    Frage(
                        feld = FELD_SYSTEMISCHES_RISIKO,
                        text = "Übersteigt der Rechenaufwand des Trainings 10^25 " +
                            "Gleitkommaoperationen, oder hat die Kommission das Modell " +
                            "als Modell mit systemischem Risiko benannt?",
                        fundstelle = regel.fundstelle,
                        regel = regel.kennung,
                        gruppe = GRUPPE_BASISMODELL,
                    )
                )
            }
        }

        if (anhangIIIGreift(beschreibung)) {
            nachArt["hochrisiko_ausnahme"].orEmpty().firstOrNull()?.let { regel ->
                liste.add(
                    Frage(
                        feld = FELD_AUSNAHME,
                        text = "Führt das System nur eine eng umgrenzte " +
                            "Verfahrensaufgabe aus, verbessert es nur das Ergebnis " +
                            "einer schon erledigten menschlichen Tätigkeit, erkennt es " +
                            "nur Entscheidungsmuster, oder bereitet es eine Bewertung " +
                            "lediglich vor - und beeinflusst es das Ergebnis der " +
                            "Entscheidung nicht wesentlich?",
                        fundstelle = regel.fundstelle,
                        regel = regel.kennung,
                        gruppe = GRUPPE_AUSNAHME,
                    )
                )
                liste.add(
                    Frage(
                        feld = FELD_PROFILING,
                        text = "Führt das System ein Profiling natürlicher Personen " +
                            "durch - bewertet es also persönliche Merkmale, um Verhalten " +
                            "oder Eigenschaften vorherzusagen?",
                        fundstelle = regel.fundstelle,
                        regel = regel.kennung,
                        gruppe = GRUPPE_AUSNAHME,
                    )
                )
            }
        }

        // Ein Feld kann in mehreren Regeln vorkommen - "emotionserkennung" steht
        // im Verbot nach Artikel 5 Absatz 1 Buchstabe f und in der
        // Transparenzpflicht nach Artikel 50 Absatz 3. Gefragt wird es einmal;
        // ausgewertet wird die Antwort in jeder Regel, die sie braucht.
        return liste.distinctBy { it.feld }
    }

    /**
     * Deutet die Beschreibung des Nutzers auf diese Regel?
     *
     * Ein Stichwort trifft, wenn alle seine Wörter in der Beschreibung
     * vorkommen - "kinder gezielt" soll auch "gezielt an Kinder" finden.
     *
     * Wichtig: ein Treffer stellt nur die FRAGE. Er stuft nichts ein. Ein
     * Wort in einem Freitext ist kein Sachverhalt.
     */
    fun deutetDarauf(regel: Risikoregel, beschreibung: String): Boolean {
        if (beschreibung.isBlank()) return false
        val flach = flach(beschreibung)
        return regel.stichworte.any { stichwort ->
            val teile = flach(stichwort).split(' ').filter { it.length > 2 }
            teile.isNotEmpty() && teile.all { it in flach }
        }
    }

    /** Die Regeln, auf die die Beschreibung deutet - für den Einstieg. */
    fun vorschlagen(beschreibung: String): List<Risikoregel> =
        regeln.filter { it.stichworte.isNotEmpty() && deutetDarauf(it, beschreibung) }

    // ------------------------------------------------------------ Einstufung

    fun pruefen(beschreibung: Systembeschreibung): Einstufung {
        val hinweise = ArrayList<Risikohinweis>()
        val offene = ArrayList<OffeneFrage>()
        val klassen = LinkedHashSet<Risikoklasse>()

        // Stufe 1: Verbote. Ein Verbot beendet die Prüfung - was verboten
        // ist, braucht keine Pflichtenliste für den erlaubten Betrieb.
        for (regel in nachArt["verbot"].orEmpty()) {
            when (bewerten(regel, beschreibung)) {
                Ergebnis.TRIFFT -> {
                    klassen.add(Risikoklasse.VERBOTEN)
                    hinweise.add(hinweisAus(regel, Risikoklasse.VERBOTEN))
                }
                Ergebnis.OFFEN -> offene.addAll(offeneAus(regel, beschreibung, FOLGE_VERBOT))
                Ergebnis.TRIFFT_NICHT -> Unit
            }
        }

        if (Risikoklasse.VERBOTEN in klassen) {
            return zusammenstellen(beschreibung, klassen, hinweise, offene)
        }

        // Stufe 2: hohes Risiko über ein Produkt nach Anhang I.
        for (regel in nachArt["hochrisiko_anhang_i"].orEmpty()) {
            when (bewerten(regel, beschreibung)) {
                Ergebnis.TRIFFT -> {
                    klassen.add(Risikoklasse.HOCHRISIKO_ANHANG_I)
                    hinweise.add(hinweisAus(regel, Risikoklasse.HOCHRISIKO_ANHANG_I))
                }
                Ergebnis.OFFEN -> offene.addAll(offeneAus(regel, beschreibung, FOLGE_HOCHRISIKO))
                Ergebnis.TRIFFT_NICHT -> Unit
            }
        }

        // Stufe 2: hohes Risiko über einen Bereich nach Anhang III. Hier
        // entscheidet die Antwort auf die Bereichsfrage, nicht ein Feld.
        for (regel in nachArt["hochrisiko_anhang_iii"].orEmpty()) {
            when (beschreibung.antwort(regel.kennung)) {
                Antwort.JA -> {
                    klassen.add(Risikoklasse.HOCHRISIKO_ANHANG_III)
                    hinweise.add(
                        hinweisAus(
                            regel, Risikoklasse.HOCHRISIKO_ANHANG_III,
                            begruendung = "Der Bereich \"${regel.titel}\" ist in " +
                                "${regel.fundstelle} als Hochrisikobereich genannt.",
                        )
                    )
                }
                Antwort.OFFEN -> Unit
                Antwort.NEIN -> Unit
            }
        }

        // Die Ausnahme nach Artikel 6 Absatz 3 - nur für Anhang III, und nur
        // wenn kein Profiling stattfindet. Das Profiling ist die
        // Gegenausnahme: sie schlägt die Ausnahme immer.
        var ausnahmeHinweis: Risikohinweis? = null
        if (Risikoklasse.HOCHRISIKO_ANHANG_III in klassen) {
            val regel = nachArt["hochrisiko_ausnahme"].orEmpty().firstOrNull()
            if (regel != null) {
                val greift = beschreibung.antwort(FELD_AUSNAHME)
                val profiling = beschreibung.antwort(FELD_PROFILING)
                if (greift == Antwort.JA && profiling == Antwort.NEIN) {
                    klassen.remove(Risikoklasse.HOCHRISIKO_ANHANG_III)
                    klassen.add(Risikoklasse.HOCHRISIKO_AUSNAHME)
                    ausnahmeHinweis = hinweisAus(
                        regel, Risikoklasse.HOCHRISIKO_AUSNAHME,
                        begruendung = regel.begruendung +
                            " Die Ausnahme ist zu dokumentieren, und das System ist " +
                            "dennoch in der Datenbank nach Artikel 49 Absatz 2 zu " +
                            "registrieren.",
                    )
                    hinweise.add(ausnahmeHinweis)
                } else if (greift == Antwort.OFFEN || profiling == Antwort.OFFEN) {
                    if (greift == Antwort.OFFEN) {
                        offene.add(
                            OffeneFrage(
                                feld = FELD_AUSNAHME, frage = regel.begruendung,
                                regel = regel.kennung, fundstelle = regel.fundstelle,
                                folgeBeiJa = FOLGE_AUSNAHME,
                            )
                        )
                    }
                    if (profiling == Antwort.OFFEN) {
                        offene.add(
                            OffeneFrage(
                                feld = FELD_PROFILING,
                                frage = "Findet ein Profiling natürlicher Personen statt?",
                                regel = regel.kennung, fundstelle = regel.fundstelle,
                                folgeBeiJa = FOLGE_PROFILING,
                            )
                        )
                    }
                }
            }
        }

        // Stufe 3: Transparenzpflichten. Sie treten NEBEN eine andere
        // Einstufung, sie ersetzen sie nicht - ein Hochrisikosystem, das mit
        // Menschen spricht, muss beides erfüllen.
        for (regel in nachArt["transparenz"].orEmpty()) {
            when (bewerten(regel, beschreibung)) {
                Ergebnis.TRIFFT -> {
                    klassen.add(Risikoklasse.TRANSPARENZ)
                    hinweise.add(hinweisAus(regel, Risikoklasse.TRANSPARENZ))
                }
                Ergebnis.OFFEN -> Unit
                Ergebnis.TRIFFT_NICHT -> Unit
            }
        }

        // Stufe 4: Modelle mit allgemeinem Verwendungszweck.
        for (regel in nachArt["gpai"].orEmpty()) {
            if (bewerten(regel, beschreibung) == Ergebnis.TRIFFT) {
                klassen.add(Risikoklasse.GPAI)
                hinweise.add(hinweisAus(regel, Risikoklasse.GPAI))
                if (beschreibung.antwort(FELD_SYSTEMISCHES_RISIKO) == Antwort.JA) {
                    nachArt["gpai_systemisch"].orEmpty().firstOrNull()?.let {
                        klassen.add(Risikoklasse.GPAI_SYSTEMISCH)
                        hinweise.add(hinweisAus(it, Risikoklasse.GPAI_SYSTEMISCH))
                    }
                }
            }
        }

        // Stufe 5: alles Übrige. Auch das ist eine Einstufung mit einer
        // Pflicht - Artikel 4 verlangt KI-Kompetenz von jedem.
        if (klassen.isEmpty()) {
            nachArt["minimal"].orEmpty().firstOrNull()?.let {
                klassen.add(Risikoklasse.MINIMAL)
                hinweise.add(hinweisAus(it, Risikoklasse.MINIMAL))
            }
        }

        return zusammenstellen(beschreibung, klassen, hinweise, offene)
    }

    // ------------------------------------------------------------- Innenteil

    private enum class Ergebnis { TRIFFT, TRIFFT_NICHT, OFFEN }

    /**
     * Prüft die Bedingungen einer Regel.
     *
     * Alle müssen zutreffen. Eine unbeantwortete Bedingung macht das Ergebnis
     * offen und NICHT negativ - sonst würde eine Frage, die der Nutzer
     * übersprungen hat, als Entlastung gelesen.
     */
    private fun bewerten(regel: Risikoregel, beschreibung: Systembeschreibung): Ergebnis {
        if (regel.bedingungen.isEmpty()) return Ergebnis.TRIFFT_NICHT
        var offen = false
        for (bedingung in regel.bedingungen) {
            when (beschreibung.antwort(bedingung.feld)) {
                Antwort.JA -> if (!bedingung.ist) return Ergebnis.TRIFFT_NICHT
                Antwort.NEIN -> if (bedingung.ist) return Ergebnis.TRIFFT_NICHT
                Antwort.OFFEN -> offen = true
            }
        }
        return if (offen) Ergebnis.OFFEN else Ergebnis.TRIFFT
    }

    private fun anhangIIIGreift(beschreibung: Systembeschreibung): Boolean =
        nachArt["hochrisiko_anhang_iii"].orEmpty()
            .any { beschreibung.antwort(it.kennung) == Antwort.JA }

    private fun hinweisAus(
        regel: Risikoregel,
        klasse: Risikoklasse,
        begruendung: String = "",
    ) = Risikohinweis(
        klasse = klasse,
        regel = regel.kennung,
        fundstelle = regel.fundstelle,
        begruendung = begruendung.ifBlank {
            regel.begruendung.ifBlank { regel.titel }
        },
        rechtsgrundlage = regel.rechtsgrundlage,
        sicherheit = regel.sicherheit,
    )

    private fun offeneAus(
        regel: Risikoregel,
        beschreibung: Systembeschreibung,
        folge: String,
    ): List<OffeneFrage> = regel.bedingungen
        .filter { beschreibung.antwort(it.feld) == Antwort.OFFEN }
        .map {
            OffeneFrage(
                feld = it.feld,
                frage = regel.frage.ifBlank { regel.titel },
                regel = regel.kennung,
                fundstelle = regel.fundstelle,
                folgeBeiJa = folge,
            )
        }

    private fun zusammenstellen(
        beschreibung: Systembeschreibung,
        klassen: Set<Risikoklasse>,
        hinweise: List<Risikohinweis>,
        offene: List<OffeneFrage>,
    ): Einstufung {
        val fuehrend = klassen.maxByOrNull { it.schwere } ?: Risikoklasse.MINIMAL
        val rollen = rollenVon(beschreibung)
        val klassenwerte = klassen.map { it.wert }.toSet().ifEmpty { setOf(fuehrend.wert) }
        val rollenwerte = rollen.map { it.wert }.toSet()

        val getroffen = pflichten
            .filter { it.trifft(rollenwerte, klassenwerte) }
            .sortedWith(compareBy({ it.giltAb ?: "" }, { it.kennung }))

        val wechsel = if (beschreibung.rolle == Rolle.BETREIBER &&
            klassen.any { it.wert.startsWith("hochrisiko") }
        ) {
            nachArt["rollenwechsel"].orEmpty().firstOrNull()?.let { regel ->
                val faelle = regel.zusatz["wird_anbieter_wenn"].orEmpty()
                "${regel.fundstelle}: ${regel.begruendung} " +
                    if (faelle.isNotBlank()) "Das gilt, wenn einer dieser Fälle vorliegt." else ""
            }.orEmpty()
        } else {
            ""
        }

        val alleOffenen = if (beschreibung.rolle == null) {
            listOf(
                OffeneFrage(
                    feld = FELD_ROLLE,
                    frage = "Sind Sie Anbieter des Systems - entwickeln oder bringen " +
                        "Sie es unter eigenem Namen in Verkehr - oder Betreiber, " +
                        "nutzen Sie es also in eigener Verantwortung?",
                    regel = "rolle",
                    fundstelle = "Artikel 3 Nummer 3 und Nummer 4 KI-VO",
                    folgeBeiJa = FOLGE_ROLLE,
                )
            ) + offene
        } else {
            offene
        }

        return Einstufung(
            klasse = fuehrend,
            weitereKlassen = klassen - fuehrend,
            rollen = rollen,
            hinweise = hinweise,
            pflichten = getroffen,
            offeneFragen = alleOffenen.distinctBy { it.feld },
            rollenwechselHinweis = wechsel,
        )
    }

    /**
     * Welche Rollen für die Pflichtenliste gelten.
     *
     * Ist die Rolle noch nicht angegeben, werden Anbieter UND Betreiber
     * genommen und die Rolle bleibt als offene Frage stehen. Eine leere
     * Pflichtenliste wäre die schlechtere Antwort: sie sieht aus wie
     * Entlastung, obwohl nur eine Angabe fehlt.
     */
    private fun rollenVon(beschreibung: Systembeschreibung): Set<Rolle> {
        val rollen = LinkedHashSet<Rolle>()
        if (beschreibung.rolle != null) {
            rollen.add(beschreibung.rolle)
        } else {
            rollen.add(Rolle.ANBIETER)
            rollen.add(Rolle.BETREIBER)
        }
        if (beschreibung.istProdukthersteller) rollen.add(Rolle.PRODUKTHERSTELLER)
        return rollen
    }

    /**
     * Macht aus einem Feldnamen eine Frage, wenn die Regel keine eigene hat.
     *
     * Die Transparenzfälle und Anhang I führen ihre Bedingungen als Felder,
     * aber nur eine Frage für die ganze Regel. Für einen Fragebogen braucht
     * jedes Feld einen Satz.
     */
    private fun frageFuerFeld(feld: String, rueckfall: String): String = when (feld) {
        "eingebaut_in_produkt" ->
            "Ist das KI-System in ein Produkt eingebaut oder selbst ein Produkt?"
        "produkt_unter_anhang_i" ->
            "Fällt dieses Produkt unter eine der Vorschriften in Anhang I der " +
                "KI-Verordnung - etwa Maschinen, Medizinprodukte, Spielzeug, Aufzüge, " +
                "Fahrzeuge, Funkanlagen?"
        "konformitaetsbewertung_durch_dritte" ->
            "Muss dieses Produkt vor dem Verkauf von einer unabhängigen Stelle " +
                "geprüft werden?"
        "interagiert_mit_menschen" ->
            "Sprechen oder schreiben Menschen unmittelbar mit dem System, etwa in " +
                "einem Dialog?"
        "erzeugt_inhalte" ->
            "Erzeugt das System Texte, Bilder, Tonaufnahmen oder Videos?"
        "emotionserkennung" ->
            "Erkennt oder erschließt das System Gefühle von Menschen?"
        "erzeugt_deepfakes" ->
            "Erzeugt oder verändert das System Bilder, Ton oder Video so, dass sie " +
                "echten Personen oder Ereignissen täuschend ähnlich sehen?"
        else -> rueckfall.ifBlank { feld.replace('_', ' ') }
    }

    private fun flach(text: String): String = text.lowercase()
        .replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")

    companion object {
        /**
         * Felder für die beiden Fragen, die Artikel 6 Absatz 3 verlangt, und
         * für das systemische Risiko. Sie stehen nicht als Feld in der
         * Regeldatei, weil die Verordnung dort keine Ja-Nein-Bedingung,
         * sondern eine Voraussetzung und eine Gegenausnahme formuliert.
         */
        const val FELD_AUSNAHME = "ausnahme_trifft_zu"
        const val FELD_PROFILING = "fuehrt_profiling_durch"
        const val FELD_SYSTEMISCHES_RISIKO = "systemisches_risiko"
        const val FELD_ROLLE = "rolle"

        const val GRUPPE_VERBOT = "Verbotene Praktiken (Artikel 5)"
        const val GRUPPE_ANHANG_III = "Bereiche mit hohem Risiko (Anhang III)"
        const val GRUPPE_ANHANG_I = "Eingebaut in ein Produkt (Anhang I)"
        const val GRUPPE_TRANSPARENZ = "Transparenz (Artikel 50)"
        const val GRUPPE_BASISMODELL = "Eigenes Modell (Artikel 51 bis 55)"
        const val GRUPPE_AUSNAHME = "Ausnahme nach Artikel 6 Absatz 3"

        private const val FOLGE_VERBOT =
            "Bei Ja ist der Einsatz verboten; die Einstufung ändert sich grundlegend."
        private const val FOLGE_HOCHRISIKO =
            "Bei Ja gilt das System als Hochrisiko-KI-System."
        private const val FOLGE_AUSNAHME =
            "Bei Ja entfallen die Hochrisikopflichten, Dokumentation und " +
                "Registrierung bleiben."
        private const val FOLGE_PROFILING =
            "Bei Ja greift die Ausnahme nicht; es bleibt beim hohen Risiko."
        private const val FOLGE_ROLLE =
            "Die Rolle entscheidet, welche Pflichten gelten."
    }
}
