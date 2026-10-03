package de.konformitaetshelfer.daten

/**
 * Eine Pflicht aus der KI-Verordnung.
 *
 * [rollen] und [klassen] entscheiden, ob die Pflicht jemanden trifft. Beide
 * sind Listen, weil dieselbe Pflicht oft Anbieter und Produkthersteller
 * gleichzeitig trifft und in mehreren Risikoklassen gilt.
 */
data class Pflicht(
    val kennung: String,
    val titel: String,
    val wasZuTunIst: String,
    val rechtsgrundlage: List<String>,
    val fundstellenText: String,
    val rollen: Set<String>,
    val klassen: Set<String>,
    val schwere: String,
    val giltAb: String?,
    val nachweis: String,
    val beiVerstoss: String,
) {
    /**
     * Trifft die Pflicht jemanden in dieser Rolle und dieser Klasse?
     *
     * Beides muss zutreffen. Wer Betreiber ist, trifft die Anbieterpflicht
     * eines Hochrisikosystems nicht - außer er wird nach Artikel 25 selbst
     * zum Anbieter, und dann steht die Rolle schon in der Einstufung.
     */
    fun trifft(rollen: Set<String>, klassen: Set<String>): Boolean =
        this.rollen.any { it in rollen } && this.klassen.any { it in klassen }
}

/**
 * Ein Abschnitt des Prüfpfads der Datenschutz-Grundverordnung.
 *
 * Die Abschnitte werden in der Reihenfolge [rang] durchgegangen; sie bauen
 * aufeinander auf. Wer den Personenbezug verneint, ist nach dem ersten
 * Abschnitt fertig.
 */
data class Pruefabschnitt(
    val kennung: String,
    val rang: Int,
    val titel: String,
    val frage: String,
    val rechtsgrundlage: List<String>,
    val fundstellenText: String,
    val wasZuTunIst: String,
    val nachweis: String,
    val beiVerstoss: String,
)
