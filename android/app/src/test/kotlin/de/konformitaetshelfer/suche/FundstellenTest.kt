package de.konformitaetshelfer.suche

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Prüft die Fundstellenerkennung.
 *
 * Wer "Artikel 6 Absatz 3" tippt, will genau diese Stelle sehen. Die
 * erzeugten Kennungen müssen auf das Haar der Schreibweise im Bestand
 * entsprechen, sonst findet die Suche nichts und fällt stillschweigend auf
 * Ähnlichkeit zurück.
 */
class FundstellenTest {

    @Test
    fun `Artikel mit Absatz wird zur Kennung`() {
        val gefunden = Fundstellen.ausFrage("Was sagt Artikel 6 Absatz 3 der KI-Verordnung?")
        assertEquals(listOf("KI-VO/art-6/abs-3"), gefunden)
    }

    @Test
    fun `Artikel mit Absatz und Buchstabe`() {
        val gefunden = Fundstellen.ausFrage("Art. 5 Abs. 1 Buchst. a der KI-VO")
        assertEquals(listOf("KI-VO/art-5/abs-1-a"), gefunden)
    }

    @Test
    fun `Paragraf wird immer dem Bundesdatenschutzgesetz zugeordnet`() {
        assertEquals(listOf("BDSG/par-26"), Fundstellen.ausFrage("§ 26 BDSG"))
    }

    @Test
    fun `Anhang mit Nummer`() {
        assertEquals(
            listOf("KI-VO/anh-III/nr-4"),
            Fundstellen.ausFrage("Anhang III Nummer 4"),
        )
    }

    @Test
    fun `Anhang ohne Nummer`() {
        assertEquals(listOf("KI-VO/anh-I"), Fundstellen.ausFrage("Anhang I"))
    }

    @Test
    fun `Erwaegungsgrund in beiden Schreibweisen`() {
        assertTrue("DSGVO/erw-60" in Fundstellen.ausFrage("Erwägungsgrund 60"))
        assertTrue("KI-VO/erw-51" in Fundstellen.ausFrage("ErwG 51 der KI-VO"))
    }

    @Test
    fun `ohne genannten Rechtsakt werden beide geliefert`() {
        val gefunden = Fundstellen.ausFrage("Was steht in Artikel 9?")
        assertEquals(listOf("KI-VO/art-9", "DSGVO/art-9"), gefunden)
    }

    @Test
    fun `die Datenschutz-Grundverordnung wird erkannt`() {
        assertEquals(
            listOf("DSGVO/art-22"),
            Fundstellen.ausFrage("Artikel 22 DSGVO zur automatisierten Entscheidung"),
        )
    }

    @Test
    fun `ohne Fundstelle kommt nichts`() {
        assertTrue(Fundstellen.ausFrage("Dürfen wir Bewerbungen vorsortieren?").isEmpty())
    }

    @Test
    fun `mehrere Fundstellen in einer Frage`() {
        val gefunden = Fundstellen.ausFrage("Artikel 6 Absatz 2 und Artikel 26 der KI-VO")
        assertEquals(listOf("KI-VO/art-6/abs-2", "KI-VO/art-26"), gefunden)
    }

    @Test
    fun `dieselbe Fundstelle zweimal genannt kommt einmal`() {
        val gefunden = Fundstellen.ausFrage("Artikel 9 KI-VO und nochmal Artikel 9 KI-VO")
        assertEquals(1, gefunden.size)
    }
}
