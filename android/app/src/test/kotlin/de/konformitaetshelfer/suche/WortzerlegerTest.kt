package de.konformitaetshelfer.suche

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Prüft den Wortzerleger.
 *
 * Der Wortschatz des echten Modells hat 250 002 Einträge und liegt als
 * Beigabe im Paket; hier wird mit einem kleinen nachgebauten Wortschatz
 * geprüft, weil es um das Verfahren geht und nicht um die Daten.
 *
 * Geprüft werden beide Hälften: das Lesen der Datei - dort lauern die
 * Maskierungen - und die Viterbi-Zerlegung.
 */
class WortzerlegerTest {

    /**
     * Ein kleiner Wortschatz in der Form, in der tokenizer.json ihn schreibt:
     * verschachtelte Paare aus Stück und Logarithmus der Wahrscheinlichkeit.
     * Das Zeichen U+2581 steht für einen Wortanfang.
     */
    private val wortschatz = """
        {
          "version": "1.0",
          "normalizer": { "type": "Precompiled", "precompiled_charsmap": "AAAA" },
          "model": {
            "type": "Unigram",
            "unk_id": 3,
            "vocab": [
              ["<s>", 0.0],
              ["<pad>", 0.0],
              ["</s>", 0.0],
              ["<unk>", 0.0],
              ["▁", -3.9],
              ["▁haus", -5.0],
              ["haus", -6.0],
              ["▁ha", -8.0],
              ["us", -7.0],
              ["▁tür", -9.0],
              ["mit\"anfuehrung", -10.0],
              ["mit\\strich", -11.0]
            ]
          }
        }
    """.trimIndent()

    private fun zerleger() = Wortzerleger.lesen(wortschatz.byteInputStream(Charsets.UTF_8))

    @Test
    fun `das ganze Wort wird dem Zerlegen in Teile vorgezogen`() {
        // Ganz: -5.0. Geteilt in "▁ha" und "us": -15.0. Viterbi nimmt das Ganze.
        val marken = zerleger().zerlegen("haus")
        assertEquals(listOf(0L, 5L, 2L), marken.toList())
    }

    @Test
    fun `Anfangs- und Endmarke stehen immer aussen`() {
        val marken = zerleger().zerlegen("haus tür")
        assertEquals(0L, marken.first())
        assertEquals(2L, marken.last())
        assertEquals(listOf(0L, 5L, 9L, 2L), marken.toList())
    }

    @Test
    fun `ein unbekanntes Zeichen wird zur unbekannten Marke`() {
        // "▁" ist im Wortschatz, "x" nicht - also Wortanfang plus unbekannt.
        val marken = zerleger().zerlegen("x")
        assertEquals(listOf(0L, 4L, 3L, 2L), marken.toList())
    }

    @Test
    fun `Maskierungen im Wortschatz werden aufgeloest`() {
        // Enthielte der Leser die Maskierung nicht, verschöbe sich ab dort
        // jede Kennzahl - und das Modell bekäme stillschweigend falsche Marken.
        val marken = zerleger().zerlegen("mit\"anfuehrung")
        assertTrue(10L in marken.toList())
        val zweite = zerleger().zerlegen("mit\\strich")
        assertTrue(11L in zweite.toList())
    }

    @Test
    fun `mehrere Leerzeichen erzeugen keine leeren Woerter`() {
        val marken = zerleger().zerlegen("haus    tür")
        assertEquals(listOf(0L, 5L, 9L, 2L), marken.toList())
    }

    @Test
    fun `die Laengengrenze wird eingehalten`() {
        val marken = zerleger().zerlegen("haus haus haus haus haus", hoechstens = 4)
        assertEquals(4, marken.size)
        assertEquals(0L, marken.first())
        assertEquals(2L, marken.last())
    }

    @Test
    fun `ohne Wortschatz bricht das Lesen ab`() {
        val ohne = """{ "model": { "type": "Unigram" } }"""
        var geworfen = false
        try {
            Wortzerleger.lesen(ohne.byteInputStream(Charsets.UTF_8))
        } catch (fehler: IllegalStateException) {
            geworfen = true
        }
        assertTrue("Ein fehlender Wortschatz muss auffallen", geworfen)
    }
}
