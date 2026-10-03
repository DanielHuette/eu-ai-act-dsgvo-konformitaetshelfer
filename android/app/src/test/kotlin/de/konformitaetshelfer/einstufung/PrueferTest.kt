package de.konformitaetshelfer.einstufung

import de.konformitaetshelfer.daten.Antwort
import de.konformitaetshelfer.daten.Bedingung
import de.konformitaetshelfer.daten.Pflicht
import de.konformitaetshelfer.daten.Risikoklasse
import de.konformitaetshelfer.daten.Risikoregel
import de.konformitaetshelfer.daten.Rolle
import de.konformitaetshelfer.daten.Systembeschreibung
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Prüft die Einstufung.
 *
 * Das ist der Teil, an dem für den Nutzer Geld hängt. Geprüft wird mit einem
 * nachgebauten kleinen Regelsatz in derselben Form, in der die Datenbank ihn
 * liefert - es geht um das Verfahren, nicht um den Inhalt der Regeldateien.
 *
 * Besonderes Augenmerk auf drei Stellen, an denen ein Fehler teuer wird:
 *  - eine unbeantwortete Frage darf nicht als Nein gelten,
 *  - die Ausnahme nach Artikel 6 Absatz 3 darf bei Profiling nicht greifen,
 *  - Transparenzpflichten treten neben eine andere Klasse und ersetzen sie nicht.
 */
class PrueferTest {

    private fun regel(
        kennung: String,
        art: String,
        rang: Int,
        klasse: String? = null,
        bedingungen: List<Bedingung> = emptyList(),
        stichworte: List<String> = emptyList(),
        titel: String = kennung,
        rolle: String? = null,
    ) = Risikoregel(
        kennung = kennung,
        art = art,
        rang = rang,
        klasse = klasse,
        rolle = rolle,
        titel = titel,
        fundstelle = "Fundstelle zu $kennung",
        rechtsgrundlage = listOf("KI-VO/art-1"),
        bedingungen = bedingungen,
        stichworte = stichworte,
        frage = "Frage zu $kennung",
        begruendung = "Begründung zu $kennung",
        sicherheit = "wahrscheinlich",
        giltAb = null,
        zusatz = emptyMap(),
    )

    private fun pflicht(
        kennung: String,
        rollen: Set<String>,
        klassen: Set<String>,
    ) = Pflicht(
        kennung = kennung,
        titel = kennung,
        wasZuTunIst = "zu tun: $kennung",
        rechtsgrundlage = listOf("KI-VO/art-1"),
        fundstellenText = "Artikel 1 KI-VO",
        rollen = rollen,
        klassen = klassen,
        schwere = "pflicht",
        giltAb = null,
        nachweis = "",
        beiVerstoss = "",
    )

    /** Ein kleiner Regelsatz, gebaut wie der echte. */
    private val regeln = listOf(
        regel(
            "v-sozialbewertung", "verbot", 1, "verboten",
            bedingungen = listOf(Bedingung("soziale_bewertung", true)),
            stichworte = listOf("social scoring", "sozialpunkte"),
        ),
        regel(
            "v-emotion-arbeit", "verbot", 2, "verboten",
            bedingungen = listOf(
                Bedingung("emotionserkennung", true),
                Bedingung("bereich_arbeit_oder_bildung", true),
            ),
            stichworte = listOf("emotionserkennung mitarbeiter"),
        ),
        regel(
            "h-anhang-i", "hochrisiko_anhang_i", 3, "hochrisiko_anhang_i",
            bedingungen = listOf(
                Bedingung("eingebaut_in_produkt", true),
                Bedingung("produkt_unter_anhang_i", true),
                Bedingung("konformitaetsbewertung_durch_dritte", true),
            ),
        ),
        regel("a3-4-beschaeftigung", "hochrisiko_anhang_iii", 4, titel = "Beschäftigung"),
        regel("a3-1-biometrie", "hochrisiko_anhang_iii", 5, titel = "Biometrie"),
        regel("h-ausnahme", "hochrisiko_ausnahme", 6, "hochrisiko_ausnahme"),
        regel(
            "t-interaktion", "transparenz", 7, "transparenz", rolle = "anbieter",
            bedingungen = listOf(Bedingung("interagiert_mit_menschen", true)),
        ),
        regel(
            "g-basismodell", "gpai", 8, "gpai",
            bedingungen = listOf(Bedingung("ist_basismodell", true)),
        ),
        regel("g-systemisch", "gpai_systemisch", 9, "gpai_systemisch"),
        regel("m-minimal", "minimal", 10, "minimal"),
        regel("r-rollenwechsel", "rollenwechsel", 11),
    )

    private val pflichten = listOf(
        pflicht("p-kompetenz", setOf("anbieter", "betreiber"), setOf("verboten",
            "hochrisiko_anhang_i", "hochrisiko_anhang_iii", "transparenz", "gpai", "minimal")),
        pflicht("p-anbieter-hochrisiko", setOf("anbieter"), setOf("hochrisiko_anhang_iii")),
        pflicht("p-betreiber-hochrisiko", setOf("betreiber"), setOf("hochrisiko_anhang_iii")),
        pflicht("p-transparenz", setOf("anbieter"), setOf("transparenz")),
        pflicht("p-gpai", setOf("anbieter"), setOf("gpai")),
    )

    private val pruefer = Pruefer(regeln, pflichten)

    // ------------------------------------------------------------- Grundfälle

    @Test
    fun `ohne jede Angabe bleibt es bei geringem Risiko`() {
        val ergebnis = pruefer.pruefen(Systembeschreibung(rolle = Rolle.BETREIBER))
        assertEquals(Risikoklasse.MINIMAL, ergebnis.klasse)
        // Auch geringes Risiko trägt eine Pflicht: die KI-Kompetenz.
        assertTrue(ergebnis.pflichten.any { it.kennung == "p-kompetenz" })
    }

    @Test
    fun `ein Verbot schlaegt alles andere`() {
        val beschreibung = Systembeschreibung(rolle = Rolle.ANBIETER)
            .mit("soziale_bewertung", Antwort.JA)
            .mit("a3-4-beschaeftigung", Antwort.JA)
        val ergebnis = pruefer.pruefen(beschreibung)
        assertEquals(Risikoklasse.VERBOTEN, ergebnis.klasse)
        // Nach einem Verbot wird nicht weiter eingestuft.
        assertFalse(Risikoklasse.HOCHRISIKO_ANHANG_III in ergebnis.weitereKlassen)
    }

    @Test
    fun `ein Verbot mit zwei Bedingungen braucht beide`() {
        val nurEine = Systembeschreibung(rolle = Rolle.BETREIBER)
            .mit("emotionserkennung", Antwort.JA)
            .mit("bereich_arbeit_oder_bildung", Antwort.NEIN)
        assertEquals(Risikoklasse.MINIMAL, pruefer.pruefen(nurEine).klasse)

        val beide = nurEine.mit("bereich_arbeit_oder_bildung", Antwort.JA)
        assertEquals(Risikoklasse.VERBOTEN, pruefer.pruefen(beide).klasse)
    }

    // --------------------------------------------- offen ist nicht nein

    @Test
    fun `eine offene Bedingung stuft nicht ein sondern fragt nach`() {
        val beschreibung = Systembeschreibung(rolle = Rolle.BETREIBER)
            .mit("emotionserkennung", Antwort.JA)
        // bereich_arbeit_oder_bildung ist unbeantwortet.
        val ergebnis = pruefer.pruefen(beschreibung)
        assertEquals(Risikoklasse.MINIMAL, ergebnis.klasse)
        assertTrue(
            "Die offene Bedingung muss als offene Frage erscheinen",
            ergebnis.offeneFragen.any { it.feld == "bereich_arbeit_oder_bildung" },
        )
    }

    @Test
    fun `eine ausdrueckliche Nein-Antwort erzeugt keine offene Frage`() {
        val beschreibung = Systembeschreibung(rolle = Rolle.BETREIBER)
            .mit("emotionserkennung", Antwort.JA)
            .mit("bereich_arbeit_oder_bildung", Antwort.NEIN)
        val ergebnis = pruefer.pruefen(beschreibung)
        assertTrue(ergebnis.offeneFragen.none { it.feld == "bereich_arbeit_oder_bildung" })
    }

    // ------------------------------------------------------- Anhang III

    @Test
    fun `ein Bereich nach Anhang III ergibt hohes Risiko`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.BETREIBER)
                .mit("a3-4-beschaeftigung", Antwort.JA)
        )
        assertEquals(Risikoklasse.HOCHRISIKO_ANHANG_III, ergebnis.klasse)
        assertTrue(ergebnis.hinweise.any { it.regel == "a3-4-beschaeftigung" })
    }

    @Test
    fun `die Ausnahme setzt das hohe Risiko herab`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.BETREIBER)
                .mit("a3-4-beschaeftigung", Antwort.JA)
                .mit(Pruefer.FELD_AUSNAHME, Antwort.JA)
                .mit(Pruefer.FELD_PROFILING, Antwort.NEIN)
        )
        assertEquals(Risikoklasse.HOCHRISIKO_AUSNAHME, ergebnis.klasse)
        assertFalse(Risikoklasse.HOCHRISIKO_ANHANG_III in ergebnis.weitereKlassen)
    }

    @Test
    fun `bei Profiling greift die Ausnahme nicht`() {
        // Die Gegenausnahme nach Artikel 6 Absatz 3: Profiling schlägt die
        // Ausnahme immer. Griffe sie hier, wäre die Auskunft gefährlich falsch.
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.BETREIBER)
                .mit("a3-4-beschaeftigung", Antwort.JA)
                .mit(Pruefer.FELD_AUSNAHME, Antwort.JA)
                .mit(Pruefer.FELD_PROFILING, Antwort.JA)
        )
        assertEquals(Risikoklasse.HOCHRISIKO_ANHANG_III, ergebnis.klasse)
    }

    @Test
    fun `solange die Ausnahmefragen offen sind bleibt es beim hohen Risiko`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.BETREIBER)
                .mit("a3-4-beschaeftigung", Antwort.JA)
                .mit(Pruefer.FELD_AUSNAHME, Antwort.JA)
        )
        assertEquals(Risikoklasse.HOCHRISIKO_ANHANG_III, ergebnis.klasse)
        assertTrue(ergebnis.offeneFragen.any { it.feld == Pruefer.FELD_PROFILING })
    }

    // ------------------------------------------------------- Anhang I

    @Test
    fun `Anhang I braucht alle drei Bedingungen`() {
        var beschreibung = Systembeschreibung(rolle = Rolle.ANBIETER)
            .mit("eingebaut_in_produkt", Antwort.JA)
            .mit("produkt_unter_anhang_i", Antwort.JA)
            .mit("konformitaetsbewertung_durch_dritte", Antwort.NEIN)
        assertEquals(Risikoklasse.MINIMAL, pruefer.pruefen(beschreibung).klasse)

        beschreibung = beschreibung.mit("konformitaetsbewertung_durch_dritte", Antwort.JA)
        assertEquals(
            Risikoklasse.HOCHRISIKO_ANHANG_I,
            pruefer.pruefen(beschreibung).klasse,
        )
    }

    // ------------------------------------------------------- Transparenz

    @Test
    fun `Transparenz tritt neben das hohe Risiko und ersetzt es nicht`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.ANBIETER)
                .mit("a3-4-beschaeftigung", Antwort.JA)
                .mit("interagiert_mit_menschen", Antwort.JA)
        )
        assertEquals(Risikoklasse.HOCHRISIKO_ANHANG_III, ergebnis.klasse)
        assertTrue(Risikoklasse.TRANSPARENZ in ergebnis.weitereKlassen)
        // Beide Pflichtenkreise müssen in der Liste stehen.
        assertTrue(ergebnis.pflichten.any { it.kennung == "p-anbieter-hochrisiko" })
        assertTrue(ergebnis.pflichten.any { it.kennung == "p-transparenz" })
    }

    @Test
    fun `Transparenz allein ist die fuehrende Klasse`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.ANBIETER)
                .mit("interagiert_mit_menschen", Antwort.JA)
        )
        assertEquals(Risikoklasse.TRANSPARENZ, ergebnis.klasse)
    }

    // ------------------------------------------------------- Basismodell

    @Test
    fun `ein eigenes Basismodell ergibt die Klasse Basismodell`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.ANBIETER).mit("ist_basismodell", Antwort.JA)
        )
        assertEquals(Risikoklasse.GPAI, ergebnis.klasse)
        assertTrue(ergebnis.pflichten.any { it.kennung == "p-gpai" })
    }

    @Test
    fun `systemisches Risiko kommt zum Basismodell hinzu`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.ANBIETER)
                .mit("ist_basismodell", Antwort.JA)
                .mit(Pruefer.FELD_SYSTEMISCHES_RISIKO, Antwort.JA)
        )
        assertEquals(Risikoklasse.GPAI_SYSTEMISCH, ergebnis.klasse)
        assertTrue(Risikoklasse.GPAI in ergebnis.weitereKlassen)
    }

    // ------------------------------------------------------------- Rollen

    @Test
    fun `die Rolle entscheidet die Pflichtenliste`() {
        val alsAnbieter = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.ANBIETER).mit("a3-4-beschaeftigung", Antwort.JA)
        )
        assertTrue(alsAnbieter.pflichten.any { it.kennung == "p-anbieter-hochrisiko" })
        assertFalse(alsAnbieter.pflichten.any { it.kennung == "p-betreiber-hochrisiko" })

        val alsBetreiber = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.BETREIBER).mit("a3-4-beschaeftigung", Antwort.JA)
        )
        assertTrue(alsBetreiber.pflichten.any { it.kennung == "p-betreiber-hochrisiko" })
        assertFalse(alsBetreiber.pflichten.any { it.kennung == "p-anbieter-hochrisiko" })
    }

    @Test
    fun `ohne angegebene Rolle gilt beides und die Rolle bleibt offen`() {
        // Eine leere Pflichtenliste sähe wie Entlastung aus, obwohl nur eine
        // Angabe fehlt. Deshalb beides zeigen und ausdrücklich nachfragen.
        val ergebnis = pruefer.pruefen(
            Systembeschreibung().mit("a3-4-beschaeftigung", Antwort.JA)
        )
        assertTrue(ergebnis.offeneFragen.any { it.feld == Pruefer.FELD_ROLLE })
        assertTrue(ergebnis.pflichten.any { it.kennung == "p-anbieter-hochrisiko" })
        assertTrue(ergebnis.pflichten.any { it.kennung == "p-betreiber-hochrisiko" })
    }

    @Test
    fun `der Betreiber eines Hochrisikosystems wird auf Artikel 25 hingewiesen`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.BETREIBER).mit("a3-4-beschaeftigung", Antwort.JA)
        )
        assertTrue(ergebnis.rollenwechselHinweis.isNotBlank())
    }

    @Test
    fun `beim Anbieter steht kein Hinweis auf einen Rollenwechsel`() {
        val ergebnis = pruefer.pruefen(
            Systembeschreibung(rolle = Rolle.ANBIETER).mit("a3-4-beschaeftigung", Antwort.JA)
        )
        assertTrue(ergebnis.rollenwechselHinweis.isBlank())
    }

    // ------------------------------------------------------------- Fragen

    @Test
    fun `Stichworte in der Beschreibung holen die passende Verbotsfrage hervor`() {
        val fragen = pruefer.fragen(Systembeschreibung(beschreibung = "Wir planen Sozialpunkte"))
        assertTrue(fragen.any { it.feld == "soziale_bewertung" })
        // Die andere Verbotsfrage gehört nicht dazu - sonst wären es 25 Fragen.
        assertFalse(fragen.any { it.feld == "bereich_arbeit_oder_bildung" })
    }

    @Test
    fun `auf Wunsch kommen alle Verbotsfragen`() {
        val fragen = pruefer.fragen(Systembeschreibung(), alleVerbote = true)
        assertTrue(fragen.any { it.feld == "soziale_bewertung" })
        assertTrue(fragen.any { it.feld == "bereich_arbeit_oder_bildung" })
    }

    @Test
    fun `die Bereiche nach Anhang III werden immer gefragt`() {
        val fragen = pruefer.fragen(Systembeschreibung())
        assertTrue(fragen.any { it.feld == "a3-4-beschaeftigung" })
        assertTrue(fragen.any { it.feld == "a3-1-biometrie" })
    }

    @Test
    fun `die Ausnahmefragen kommen erst nach einem Ja bei Anhang III`() {
        assertFalse(
            pruefer.fragen(Systembeschreibung()).any { it.feld == Pruefer.FELD_AUSNAHME }
        )
        val danach = pruefer.fragen(
            Systembeschreibung().mit("a3-4-beschaeftigung", Antwort.JA)
        )
        assertTrue(danach.any { it.feld == Pruefer.FELD_AUSNAHME })
        assertTrue(danach.any { it.feld == Pruefer.FELD_PROFILING })
    }

    @Test
    fun `jede Frage kommt nur einmal`() {
        val fragen = pruefer.fragen(Systembeschreibung(), alleVerbote = true)
        assertEquals(fragen.size, fragen.distinctBy { it.feld }.size)
    }

    @Test
    fun `jede Frage nennt ihre Fundstelle`() {
        // Ohne Fundstelle wüsste der Nutzer nicht, warum er das gefragt wird.
        val fragen = pruefer.fragen(Systembeschreibung(), alleVerbote = true)
        assertTrue(fragen.isNotEmpty())
        assertTrue(fragen.all { it.fundstelle.isNotBlank() })
    }

    @Test
    fun `ein Stichwort trifft auch bei anderer Wortstellung`() {
        val regel = regeln.first { it.kennung == "v-emotion-arbeit" }
        assertTrue(
            pruefer.deutetDarauf(regel, "Wir messen die Emotionserkennung bei Mitarbeitern")
        )
        assertFalse(pruefer.deutetDarauf(regel, "Wir sortieren Rechnungen"))
    }

    @Test
    fun `eine leere Beschreibung deutet auf nichts`() {
        val regel = regeln.first { it.kennung == "v-sozialbewertung" }
        assertFalse(pruefer.deutetDarauf(regel, ""))
    }
}
