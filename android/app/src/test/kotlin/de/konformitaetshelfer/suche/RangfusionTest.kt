package de.konformitaetshelfer.suche

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Prüft die Rangfusion.
 *
 * Die Rechnung ist der Kern der Suche. Geht sie falsch, liefert die App
 * plausible aber falsch sortierte Belege - der Fehler, den niemand bemerkt.
 */
class RangfusionTest {

    @Test
    fun `erster Platz eines Wegs bekommt 1 durch 61`() {
        val ergebnis = Rangfusion.verschmelzen(
            wege = mapOf("stichwort" to listOf(7)),
            gewichte = mapOf("stichwort" to 1.0),
        )
        assertEquals(1, ergebnis.size)
        assertEquals(7, ergebnis[0].nummer)
        assertEquals(1.0 / 61.0, ergebnis[0].punktzahl, 1e-12)
    }

    @Test
    fun `was zwei Wege finden steht vor dem was nur einer findet`() {
        // 5 steht auf beiden Wegen auf Platz 2, 9 nur auf einem Weg auf Platz 1.
        val ergebnis = Rangfusion.verschmelzen(
            wege = mapOf(
                "stichwort" to listOf(9, 5),
                "vektor" to listOf(3, 5),
            ),
            gewichte = mapOf("stichwort" to 1.0, "vektor" to 1.0),
        )
        assertEquals(5, ergebnis[0].nummer)
        assertEquals(2.0 / 62.0, ergebnis[0].punktzahl, 1e-12)
        assertEquals(setOf("stichwort", "vektor"), ergebnis[0].wege)
    }

    @Test
    fun `der Fundstellenweg wiegt dreifach`() {
        // Platz 1 im Fundstellenweg muss Platz 1 im Stichwortweg schlagen.
        val ergebnis = Rangfusion.verschmelzen(
            wege = mapOf(
                Suche.WEG_FUNDSTELLE to listOf(100),
                Suche.WEG_STICHWORT to listOf(200),
            ),
            gewichte = Suche.GEWICHTE,
        )
        assertEquals(100, ergebnis[0].nummer)
        assertEquals(3.0 / 61.0, ergebnis[0].punktzahl, 1e-12)
        assertEquals(200, ergebnis[1].nummer)
    }

    @Test
    fun `ein unbekannter Weg wiegt einfach`() {
        val ergebnis = Rangfusion.verschmelzen(
            wege = mapOf("neuerweg" to listOf(1)),
            gewichte = emptyMap(),
        )
        assertEquals(1.0 / 61.0, ergebnis[0].punktzahl, 1e-12)
    }

    @Test
    fun `die Reihenfolge ist absteigend und bei Gleichstand nach Nummer`() {
        val ergebnis = Rangfusion.verschmelzen(
            wege = mapOf("a" to listOf(50), "b" to listOf(20)),
            gewichte = mapOf("a" to 1.0, "b" to 1.0),
        )
        // Beide stehen auf Platz 1 ihres Wegs, haben also dieselbe Punktzahl.
        assertEquals(ergebnis[0].punktzahl, ergebnis[1].punktzahl, 1e-12)
        assertEquals(20, ergebnis[0].nummer)
        assertEquals(50, ergebnis[1].nummer)
    }

    @Test
    fun `ohne Treffer kommt eine leere Liste`() {
        assertTrue(Rangfusion.verschmelzen(emptyMap(), Suche.GEWICHTE).isEmpty())
    }

    @Test
    fun `tiefe Plaetze wiegen weniger als hohe`() {
        val ergebnis = Rangfusion.verschmelzen(
            wege = mapOf("a" to (1..50).toList()),
            gewichte = mapOf("a" to 1.0),
        )
        assertEquals(50, ergebnis.size)
        assertEquals(1, ergebnis.first().nummer)
        assertEquals(50, ergebnis.last().nummer)
        assertTrue(ergebnis.first().punktzahl > ergebnis.last().punktzahl)
    }
}
