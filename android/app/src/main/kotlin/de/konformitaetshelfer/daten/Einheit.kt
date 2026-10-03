package de.konformitaetshelfer.daten

/**
 * Eine Rechtseinheit aus dem Bestand: ein Artikel, ein Absatz, ein Paragraf,
 * ein Anhangspunkt, ein Erwägungsgrund oder ein Anwendungsfall.
 *
 * Der Wortlaut steht vollständig in [text] und wird in der Oberfläche
 * ungekürzt angezeigt. Eine Auskunft, die den Beleg zusammenfasst, nimmt dem
 * Nutzer die Möglichkeit, selbst nachzulesen - genau das ist aber der Zweck.
 */
data class Einheit(
    val nummer: Int,
    val kennung: String,
    val rechtsakt: String,
    val art: String,
    val nummerImAkt: String,
    val absatz: String?,
    val titel: String,
    val text: String,
    val fundstelle: String,
    val quelle: String,
) {
    /** Ob die Einheit ein Anwendungsfall ist und kein Gesetzestext. */
    val istAnwendungsfall: Boolean get() = art == "fallbeispiel"
}

/**
 * Ein Suchtreffer samt der Begründung, wie er gefunden wurde.
 *
 * [wege] sagt, über welche Suchwege die Einheit kam. Die Angabe steckt nicht
 * in der Oberfläche, sondern dient der Reihenfolge: was mehrere Wege
 * gleichzeitig finden, steht wahrscheinlich richtig oben.
 */
data class Treffer(
    val einheit: Einheit,
    val punktzahl: Double,
    val wege: Set<String>,
)
