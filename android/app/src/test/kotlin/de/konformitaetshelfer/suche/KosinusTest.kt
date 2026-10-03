package de.konformitaetshelfer.suche

import de.konformitaetshelfer.daten.Vektorblock
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Prüft die Vektorsuche.
 *
 * Die Reihen sind beim Bauen auf Länge 1 gebracht, deshalb ist das
 * Skalarprodukt schon das Kosinusmaß. Stimmte die Zuordnung von Zeile zu
 * Einheitsnummer nicht, zeigte die App zum richtigen Treffer den falschen
 * Text - und das fällt niemandem auf.
 */
class KosinusTest {

    /** Drei Einheiten in drei Dimensionen, jede auf eine Achse gelegt. */
    private fun block() = Vektorblock(
        nummern = intArrayOf(11, 22, 33),
        werte = floatArrayOf(
            1f, 0f, 0f,
            0f, 1f, 0f,
            0f, 0f, 1f,
        ),
        dimensionen = 3,
    )

    @Test
    fun `die gleichgerichtete Reihe gewinnt`() {
        val ergebnis = Kosinus.naechste(floatArrayOf(0f, 1f, 0f), block(), 3)
        assertEquals(22, ergebnis[0].first)
        assertEquals(1.0f, ergebnis[0].second, 1e-6f)
    }

    @Test
    fun `die Nummer der Einheit wird mitgefuehrt und nicht die Zeile`() {
        val ergebnis = Kosinus.naechste(floatArrayOf(0f, 0f, 1f), block(), 1)
        assertEquals(1, ergebnis.size)
        assertEquals(33, ergebnis[0].first)
    }

    @Test
    fun `die Reihenfolge ist absteigend`() {
        // Zeigt schräg auf die erste und zweite Achse, mehr auf die erste.
        val ergebnis = Kosinus.naechste(floatArrayOf(0.8f, 0.6f, 0f), block(), 3)
        assertEquals(listOf(11, 22, 33), ergebnis.map { it.first })
        assertTrue(ergebnis[0].second > ergebnis[1].second)
        assertTrue(ergebnis[1].second > ergebnis[2].second)
    }

    @Test
    fun `es kommen nie mehr Treffer als verlangt`() {
        assertEquals(2, Kosinus.naechste(floatArrayOf(1f, 1f, 1f), block(), 2).size)
    }

    @Test
    fun `eine entgegengesetzte Reihe bekommt ein negatives Mass`() {
        val ergebnis = Kosinus.naechste(floatArrayOf(-1f, 0f, 0f), block(), 3)
        assertEquals(11, ergebnis.last().first)
        assertEquals(-1.0f, ergebnis.last().second, 1e-6f)
    }
}
