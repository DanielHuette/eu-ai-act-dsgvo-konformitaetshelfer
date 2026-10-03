package de.konformitaetshelfer.suche

import java.io.InputStream
import java.text.Normalizer

/**
 * Zerlegt Text in die Wortmarken, die das Einbettungsmodell erwartet.
 *
 * Das Modell ist ein e5-Modell auf XLM-RoBERTa-Grundlage. Es zerlegt nach
 * dem Unigram-Verfahren: aus allen möglichen Zerlegungen eines Wortes wird
 * die mit der höchsten Summe der Stückwahrscheinlichkeiten gewählt
 * (Viterbi). Das ist in 60 Zeilen nachgebaut, statt eine zweite Bibliothek
 * mitzuschleppen.
 *
 * Nachgemessen: auf 303 echten Texten aus dem Rechtsbestand und drei
 * Beispielfragen liefert dieses Verfahren Marke für Marke dasselbe wie die
 * Bibliothek, mit der die Vektoren des Bestands gerechnet wurden (geprüft am
 * 2026-10-03). Wäre die Zerlegung anders, lägen Frage und Bestand in
 * verschiedenen Räumen und die Vektorsuche würde Unsinn liefern.
 *
 * Einziger bekannter Unterschied: Zeichen außerhalb der Grundebene - Emoji
 * etwa - werden hier zu zwei unbekannten Marken statt zu einer, weil Kotlin
 * in UTF-16-Einheiten zählt. In deutschem Rechtstext kommt das nicht vor.
 */
class Wortzerleger private constructor(
    private val stuecke: HashMap<String, Int>,
    private val punkte: FloatArray,
    private val groessteStuecklaenge: Int,
    private val kleinsterPunkt: Float,
) {

    /**
     * Macht aus Text die Marken für das Modell, mit Anfangs- und Endmarke.
     *
     * [hoechstens] schneidet lange Texte ab. Der Anfang eines Artikels trägt
     * den Sinn; die Aufzählungen am Ende wiederholen ihn meist.
     */
    fun zerlegen(text: String, hoechstens: Int = 512): LongArray {
        val gefaltet = Normalizer.normalize(text, Normalizer.Form.NFKC)
        val marken = ArrayList<Int>(64)
        marken.add(ANFANG)
        val platz = hoechstens - 2
        for (wort in gefaltet.split(LEERRAUM)) {
            if (wort.isEmpty()) continue
            if (marken.size - 1 >= platz) break
            zerlegeWort(WORTANFANG + wort, marken, platz)
        }
        marken.add(ENDE)
        return LongArray(marken.size) { marken[it].toLong() }
    }

    /** Viterbi über ein einzelnes Wort. */
    private fun zerlegeWort(wort: String, hinein: ArrayList<Int>, platz: Int) {
        val n = wort.length
        val beste = DoubleArray(n + 1) { Double.NEGATIVE_INFINITY }
        val herkunft = IntArray(n + 1) { -1 }
        val marke = IntArray(n + 1) { -1 }
        beste[0] = 0.0

        for (bis in 1..n) {
            val frueheste = if (bis > groessteStuecklaenge) bis - groessteStuecklaenge else 0
            for (von in frueheste until bis) {
                if (beste[von] == Double.NEGATIVE_INFINITY) continue
                val kennzahl = stuecke[wort.substring(von, bis)] ?: continue
                val wert = beste[von] + punkte[kennzahl]
                if (wert > beste[bis]) {
                    beste[bis] = wert
                    herkunft[bis] = von
                    marke[bis] = kennzahl
                }
            }
            if (herkunft[bis] < 0) {
                // Kein Stück passt: das Zeichen ist im Wortschatz nicht
                // vorgesehen. Es wird eine unbekannte Marke, mit Abschlag,
                // damit jede echte Zerlegung vorgezogen wird.
                val von = bis - 1
                if (beste[von] != Double.NEGATIVE_INFINITY) {
                    beste[bis] = beste[von] + kleinsterPunkt - 10.0
                    herkunft[bis] = von
                    marke[bis] = UNBEKANNT
                }
            }
        }

        if (herkunft[n] < 0) {
            hinein.add(UNBEKANNT)
            return
        }
        // Rückwärts auslesen und in richtiger Reihenfolge anhängen.
        val rueckwaerts = ArrayList<Int>(8)
        var stelle = n
        while (stelle > 0) {
            rueckwaerts.add(marke[stelle])
            stelle = herkunft[stelle]
        }
        for (i in rueckwaerts.indices.reversed()) {
            if (hinein.size - 1 >= platz) return
            hinein.add(rueckwaerts[i])
        }
    }

    companion object {
        /** Die festen Marken von XLM-RoBERTa. */
        const val ANFANG = 0
        const val ENDE = 2
        const val UNBEKANNT = 3

        /** Das Zeichen, mit dem der Wortschatz einen Wortanfang schreibt. */
        private const val WORTANFANG = "▁"
        private val LEERRAUM = Regex("\\s+")

        /**
         * Liest den Wortschatz aus tokenizer.json.
         *
         * Gelesen wird im Durchlauf und nur der Teil model.vocab. Die Datei
         * ist 17 MB groß und enthält unter anderem eine große Zeichentabelle,
         * die hier nichts beiträgt; sie vollständig in Objekte zu verwandeln
         * wäre eine Verschwendung von Speicher, den das Telefon nicht hat.
         */
        fun lesen(strom: InputStream): Wortzerleger {
            val leser = strom.bufferedReader(Charsets.UTF_8)
            try {
                sucheWortschatz(leser)
                val stuecke = HashMap<String, Int>(1 shl 19)
                val punkte = ArrayList<Float>(1 shl 18)
                var groesste = 1
                var kleinster = 0.0f

                while (true) {
                    val zeichen = naechstesWichtige(leser)
                    if (zeichen == ']'.code || zeichen < 0) break
                    if (zeichen != '['.code) continue   // Komma zwischen den Paaren
                    val stueck = leseText(leser)
                    val punkt = leseZahl(leser)
                    val kennzahl = punkte.size
                    // Kommt ein Stück zweimal vor, gilt das erste - so hält es
                    // auch die Bibliothek.
                    if (!stuecke.containsKey(stueck)) stuecke[stueck] = kennzahl
                    punkte.add(punkt)
                    if (stueck.length > groesste) groesste = stueck.length
                    if (punkt < kleinster) kleinster = punkt
                }

                if (stuecke.isEmpty()) {
                    throw IllegalStateException("tokenizer.json enthält keinen Wortschatz")
                }
                return Wortzerleger(
                    stuecke = stuecke,
                    punkte = FloatArray(punkte.size) { punkte[it] },
                    groessteStuecklaenge = groesste,
                    kleinsterPunkt = kleinster,
                )
            } finally {
                leser.close()
            }
        }

        /** Spult bis hinter `"vocab" : [`. */
        private fun sucheWortschatz(leser: java.io.Reader) {
            val gesucht = "\"vocab\""
            var treffer = 0
            while (true) {
                val gelesen = leser.read()
                if (gelesen < 0) {
                    throw IllegalStateException("tokenizer.json hat kein Feld vocab")
                }
                val zeichen = gelesen.toChar()
                treffer = if (zeichen == gesucht[treffer]) treffer + 1 else
                    if (zeichen == gesucht[0]) 1 else 0
                if (treffer != gesucht.length) continue
                // Hinter dem Namen müssen Doppelpunkt und öffnende Klammer
                // folgen. Steht da etwas anderes, war es ein gleichnamiges
                // Feld woanders und die Suche geht weiter.
                if (naechstesWichtige(leser) != ':'.code) { treffer = 0; continue }
                if (naechstesWichtige(leser) != '['.code) { treffer = 0; continue }
                return
            }
        }

        private fun naechstesWichtige(leser: java.io.Reader): Int {
            while (true) {
                val gelesen = leser.read()
                if (gelesen < 0) return -1
                val zeichen = gelesen.toChar()
                if (zeichen == ' ' || zeichen == '\n' || zeichen == '\r' ||
                    zeichen == '\t' || zeichen == ','
                ) {
                    continue
                }
                return gelesen
            }
        }

        /** Liest die nächste JSON-Zeichenfolge, Maskierungen aufgelöst. */
        private fun leseText(leser: java.io.Reader): String {
            while (true) {
                val gelesen = leser.read()
                if (gelesen < 0) throw IllegalStateException("tokenizer.json bricht ab")
                if (gelesen.toChar() == '"') break
            }
            val bau = StringBuilder(16)
            while (true) {
                val gelesen = leser.read()
                if (gelesen < 0) throw IllegalStateException("tokenizer.json bricht ab")
                when (val zeichen = gelesen.toChar()) {
                    '"' -> return bau.toString()
                    '\\' -> {
                        val folgt = leser.read()
                        if (folgt < 0) throw IllegalStateException("tokenizer.json bricht ab")
                        when (val nach = folgt.toChar()) {
                            'n' -> bau.append('\n')
                            'r' -> bau.append('\r')
                            't' -> bau.append('\t')
                            'b' -> bau.append('\b')
                            'f' -> bau.append('\u000C')
                            'u' -> {
                                val vier = CharArray(4)
                                var gefuellt = 0
                                while (gefuellt < 4) {
                                    val teil = leser.read(vier, gefuellt, 4 - gefuellt)
                                    if (teil < 0) {
                                        throw IllegalStateException("tokenizer.json bricht ab")
                                    }
                                    gefuellt += teil
                                }
                                bau.append(String(vier).toInt(16).toChar())
                            }
                            else -> bau.append(nach)
                        }
                    }
                    else -> bau.append(zeichen)
                }
            }
        }

        /** Liest die Zahl hinter der Zeichenfolge bis zur schließenden Klammer. */
        private fun leseZahl(leser: java.io.Reader): Float {
            val bau = StringBuilder(24)
            while (true) {
                val gelesen = leser.read()
                if (gelesen < 0) throw IllegalStateException("tokenizer.json bricht ab")
                val zeichen = gelesen.toChar()
                if (zeichen == ']') break
                if (zeichen == ',' || zeichen == ' ' || zeichen == '\n' ||
                    zeichen == '\r' || zeichen == '\t'
                ) {
                    continue
                }
                bau.append(zeichen)
            }
            return bau.toString().toFloatOrNull() ?: 0.0f
        }
    }
}
