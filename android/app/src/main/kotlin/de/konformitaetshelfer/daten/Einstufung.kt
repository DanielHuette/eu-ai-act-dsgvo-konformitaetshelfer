package de.konformitaetshelfer.daten

/**
 * Die Schubladen der KI-Verordnung.
 *
 * Die Zeichenfolge in [wert] ist dieselbe wie in den Regeldateien und in der
 * Datenbank. Sie wird nicht übersetzt, weil sonst an jeder Grenze zwischen
 * Daten und Programm eine Umrechnung stünde, die irgendwann abweicht.
 */
enum class Risikoklasse(val wert: String, val anzeige: String, val schwere: Int) {
    VERBOTEN("verboten", "Verbotene Praktik", 5),
    HOCHRISIKO_ANHANG_I("hochrisiko_anhang_i", "Hohes Risiko (Produkt nach Anhang I)", 4),
    HOCHRISIKO_ANHANG_III("hochrisiko_anhang_iii", "Hohes Risiko (Bereich nach Anhang III)", 4),
    HOCHRISIKO_AUSNAHME("hochrisiko_ausnahme", "Ausnahme vom hohen Risiko", 3),
    GPAI_SYSTEMISCH("gpai_systemisch", "Basismodell mit systemischem Risiko", 3),
    GPAI("gpai", "Basismodell", 2),
    TRANSPARENZ("transparenz", "Transparenzpflichten", 2),
    MINIMAL("minimal", "Geringes Risiko", 1);

    companion object {
        fun ausWert(wert: String?): Risikoklasse? = entries.firstOrNull { it.wert == wert }
    }
}

/** Wer jemand im Sinne der Verordnung ist. Die Rolle entscheidet die Pflichten. */
enum class Rolle(val wert: String, val anzeige: String) {
    ANBIETER("anbieter", "Anbieter"),
    BETREIBER("betreiber", "Betreiber"),
    EINFUEHRER("einfuehrer", "Einführer"),
    HAENDLER("haendler", "Händler"),
    PRODUKTHERSTELLER("produkthersteller", "Produkthersteller"),
    BEVOLLMAECHTIGTER("bevollmaechtigter", "Bevollmächtigter");

    companion object {
        fun ausWert(wert: String?): Rolle? = entries.firstOrNull { it.wert == wert }
    }
}

/** Eine Bedingung aus dem Entscheidungsbaum: ein Feld muss einen Wert haben. */
data class Bedingung(val feld: String, val ist: Boolean)

/**
 * Eine Regel des Entscheidungsbaums, wie sie in der Tabelle risikoregel steht.
 *
 * [art] sagt, an welcher Stelle des Baums sie hängt, [rang] in welcher
 * Reihenfolge geprüft wird. Beides kommt aus den Daten: eine Rechtsänderung
 * soll die Regeldatei ändern und nicht diese Klasse.
 */
data class Risikoregel(
    val kennung: String,
    val art: String,
    val rang: Int,
    val klasse: String?,
    val rolle: String?,
    val titel: String,
    val fundstelle: String,
    val rechtsgrundlage: List<String>,
    val bedingungen: List<Bedingung>,
    val stichworte: List<String>,
    val frage: String,
    val begruendung: String,
    val sicherheit: String,
    val giltAb: String?,
    val zusatz: Map<String, String>,
)

/** Was der Nutzer auf eine Frage geantwortet hat. */
enum class Antwort { JA, NEIN, OFFEN }

/**
 * Was der Nutzer über sein System angegeben hat.
 *
 * [angaben] sind die beantworteten Fragen, gekennzeichnet nach dem Feldnamen
 * der Regel oder - bei den Bereichen des Anhangs III - nach der Kennung des
 * Bereichs. Was nicht drinsteht, gilt als offen und erscheint am Ende als
 * offene Frage, nicht als Nein. Der Unterschied ist wichtig: eine
 * unbeantwortete Frage darf keine Entlastung vortäuschen.
 */
data class Systembeschreibung(
    val beschreibung: String = "",
    val angaben: Map<String, Antwort> = emptyMap(),
    val rolle: Rolle? = null,
    val istProdukthersteller: Boolean = false,
) {
    fun antwort(feld: String): Antwort = angaben[feld] ?: Antwort.OFFEN

    fun mit(feld: String, antwort: Antwort): Systembeschreibung =
        copy(angaben = angaben + (feld to antwort))
}

/** Warum eine Klasse gezogen wurde - erscheint als Begründung in der Auskunft. */
data class Risikohinweis(
    val klasse: Risikoklasse,
    val regel: String,
    val fundstelle: String,
    val begruendung: String,
    val rechtsgrundlage: List<String>,
    val sicherheit: String,
)

/** Eine Frage, die noch zu beantworten ist, damit die Einstufung trägt. */
data class OffeneFrage(
    val feld: String,
    val frage: String,
    val regel: String,
    val fundstelle: String,
    /** Was die Antwort ändern würde - damit erkennbar ist, ob sie zählt. */
    val folgeBeiJa: String,
)

/**
 * Das Ergebnis der Einstufung.
 *
 * Es entsteht ausschließlich aus dem Entscheidungsbaum. Ein Sprachmodell
 * formuliert es auf Wunsch aus, verändert es aber nie - siehe den Kommentar
 * in [de.konformitaetshelfer.modell.Antwortgeber].
 */
data class Einstufung(
    val klasse: Risikoklasse,
    val weitereKlassen: Set<Risikoklasse> = emptySet(),
    val rollen: Set<Rolle> = emptySet(),
    val hinweise: List<Risikohinweis> = emptyList(),
    val pflichten: List<Pflicht> = emptyList(),
    val offeneFragen: List<OffeneFrage> = emptyList(),
    /** Wird aus Artikel 25 gefüllt, wenn der Betreiber zum Anbieter werden kann. */
    val rollenwechselHinweis: String = "",
) {
    /** Alle Klassen, nach denen Pflichten zu suchen sind. */
    val alleKlassen: Set<String>
        get() = (weitereKlassen + klasse).map { it.wert }.toSet()
}
