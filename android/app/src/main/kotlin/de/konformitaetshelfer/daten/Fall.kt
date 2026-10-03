package de.konformitaetshelfer.daten

/**
 * Ein ausgearbeiteter Anwendungsfall.
 *
 * Der Lernteil der App. Ein fremder Fall, der dem eigenen gleicht, erklärt
 * eine Einstufung besser als der Verordnungstext - und [stolperstein] nennt
 * den Fehler, den an dieser Stelle die meisten machen.
 */
data class Fall(
    val kennung: String,
    val gebiet: String,
    val titel: String,
    val lage: String,
    val rolle: String,
    val einstufung: String,
    val begruendung: String,
    val rechtsgrundlage: List<String>,
    val pflichten: List<String>,
    val lernhinweis: String,
    val stolperstein: String,
    val verwandteFaelle: List<String>,
)
