package de.konformitaetshelfer.suche

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Prüft den Bau der Stichwortabfrage.
 *
 * Zwei Gefahren: eine Frage mit Anführungszeichen oder dem Wort OR zerlegt
 * die FTS5-Abfrage, und eine mit ae statt ä findet nichts, weil im Index die
 * gefaltete Form steht.
 */
class StichwortabfrageTest {

    @Test
    fun `jedes Wort steht in Anfuehrungszeichen`() {
        assertEquals("\"bewerbungen\"", Stichwortabfrage.bauen("Bewerbungen"))
    }

    @Test
    fun `mehrere Woerter werden mit OR verbunden`() {
        val abfrage = Stichwortabfrage.bauen("Bewerbungen sortieren")
        assertEquals("\"bewerbungen\" OR \"sortieren\"", abfrage)
    }

    @Test
    fun `Fuellwoerter fallen heraus`() {
        val abfrage = Stichwortabfrage.bauen("Was ist mit der Einwilligung und dem Widerruf")
        assertFalse("\"ist\"" in abfrage)
        assertFalse("\"und\"" in abfrage)
        assertFalse("\"der\"" in abfrage)
        assertTrue("\"einwilligung\"" in abfrage)
        assertTrue("\"widerruf\"" in abfrage)
    }

    @Test
    fun `ae wird zusaetzlich als gefaltete Form gefragt`() {
        // Im Index steht "beschaftigte", weil der Zerteiler mit
        // remove_diacritics gebaut ist. Wer "Beschaeftigte" tippt, muss
        // trotzdem treffen.
        val abfrage = Stichwortabfrage.bauen("Beschaeftigte")
        assertTrue("\"beschaeftigte\"" in abfrage)
        assertTrue("\"beschaftigte\"" in abfrage)
    }

    @Test
    fun `Anfuehrungszeichen koennen die Abfrage nicht zerlegen`() {
        // Ein einzelnes Anführungszeichen würde die Abfrage abbrechen. Es
        // fällt schon bei der Wortzerlegung heraus, weil es kein Buchstabe ist.
        val abfrage = Stichwortabfrage.bauen("\"Hochrisiko\"")
        assertEquals("\"hochrisiko\"", abfrage)
    }

    @Test
    fun `Befehlswoerter von FTS5 werden entschaerft`() {
        // AND, OR, NOT und NEAR sind in FTS5 Befehle. In Anführungszeichen
        // sind sie gewöhnliche Wörter.
        val abfrage = Stichwortabfrage.bauen("Risiko NEAR Bewertung")
        assertTrue("\"near\"" in abfrage)
        assertFalse(abfrage.contains(" NEAR "))
    }

    @Test
    fun `Sternchen und Klammern verschwinden`() {
        val abfrage = Stichwortabfrage.bauen("Risiko* (Bewertung)")
        assertFalse("*" in abfrage)
        assertFalse("(" in abfrage)
        assertEquals("\"risiko\" OR \"bewertung\"", abfrage)
    }

    @Test
    fun `eine Frage ohne brauchbare Woerter ergibt eine leere Abfrage`() {
        assertEquals("", Stichwortabfrage.bauen("und oder in ?!"))
        assertEquals("", Stichwortabfrage.bauen("   "))
    }

    @Test
    fun `Umlaute werden wie im Index gefaltet`() {
        assertEquals("beschaftigte", Stichwortabfrage.wieImIndex("beschäftigte"))
        assertEquals("beschaeftigte", Stichwortabfrage.mitAe("beschäftigte"))
        assertEquals("gross", Stichwortabfrage.wieImIndex("groß"))
    }
}
